"""Native-method doubles only: zero actual normal/native/model/C/allocator queries.

Do not run before DM publication. Native fixture assertions below accept an
already collected snapshot; they never construct an environment or regenerate it.
"""

import numpy as np
import pytest

from experiments.candidates.uav_radio_uncertainty.b01 import contract as c, environment as e


def assert_host_snapshot(snapshot):
    """Reusable inside the already-budgeted H8 collection; no additional query."""
    assert isinstance(snapshot['world'], int) and snapshot['world'] >= 0
    assert isinstance(snapshot['tick'], int) and snapshot['tick'] >= 0
    for name, shape in (('positions',(5,3)),('users',(50,2)),('residual',(5,50)),('user_loss',(5,50))):
        assert snapshot[name].shape == shape and snapshot[name].dtype == np.float64
        assert np.isfinite(snapshot[name]).all()
    assert snapshot['sinr'].shape == (5,50) and snapshot['sinr'].dtype == np.float64
    assert snapshot['peer_sinr'].shape == (5,5) and snapshot['peer_sinr'].dtype == np.float64
    assert snapshot['connections'].shape == (5,50) and snapshot['connections'].dtype == bool
    assert snapshot['transmitter_mask'].shape == (5,) and snapshot['transmitter_mask'].dtype == bool
    active = snapshot['transmitter_mask']
    assert np.isfinite(snapshot['sinr'][active]).all() and np.isneginf(snapshot['sinr'][~active]).all()
    assert np.all(snapshot['connections'].sum(axis=1) <= c.CAPACITY)
    assert np.all(snapshot['connections'].sum(axis=0) <= 1)
    assert np.all(~snapshot['connections'] | (snapshot['sinr'] >= c.MIN_SINR_DB))
    assert all(isinstance(value,int) and value >= 0 for value in snapshot['counters'].values())


@pytest.fixture
def doubled_native(monkeypatch):
    calls = []
    def normals(world,tick):
        calls.append((world,tick))
        return np.arange(250,dtype=np.float64).reshape(5,50)/1000 + tick + world%10
    monkeypatch.setattr(e,'physical_normals',normals)

    def initialize(self, **kwargs):
        for name,value in kwargs.items():
            setattr(self,name,value)
        self.seed_val = kwargs['seed']
        self.carrier_frequency,self.tx_power,self.noise_power = c.CARRIER_HZ,c.TRANSMIT_DBM,c.NOISE_DBM
        self.min_sinr,self.max_connections = c.MIN_SINR_DB,c.CAPACITY
        self.possible_agents = [f'uav_{i}' for i in range(5)]
        self.agents = self.possible_agents.copy()
        self._ready = False
        self.reset(seed=kwargs['seed'])  # Exactly one implicit constructor reset.

    def reset(self,seed=None,options=None):
        if seed is not None:
            self.seed_val = int(seed)
            self.np_random = object()  # Opaque stand-in, not any real RNG construction.
        self.current_step = 0
        self.agents = self.possible_agents.copy()
        self._transmitter_mask = np.ones(5,bool)
        self.uav_positions = np.array([[1000.,0.,150.],[100.,200.,70.],[300.,400.,120.],
                                      [500.,600.,80.],[700.,800.,110.]])
        self.user_positions = np.column_stack((np.arange(50)*19.,np.arange(50)*17.)) + self.seed_val%3
        self._begin_path_loss_step()
        self._update_channel_state()
        return {agent:self._get_observation(agent) for agent in self.agents}, {agent:{} for agent in self.agents}

    def begin(self):
        self._ready = False

    def update(self,reuse_physical_channel=False):
        self._uav_user_path_loss_matrix = self._compute_path_loss_matrix()
        self._uav_uav_path_loss_matrix = self._compute_uav_path_loss_matrix()
        self.sinr_matrix = self.tx_power-self._uav_user_path_loss_matrix-self.noise_power
        self.sinr_matrix[~self._transmitter_mask] = -np.inf
        self.uav_sinr_matrix = self.tx_power-self._uav_uav_path_loss_matrix-self.noise_power
        self.uav_sinr_matrix[~(self._transmitter_mask[:,None]&self._transmitter_mask[None,:])] = -np.inf
        self.connections = np.zeros((5,50),bool)  # No allocator is invoked by doubles.
        self._ready = True

    def observation(self,agent):
        row = np.zeros(104,np.float32)
        i = self.agents.index(agent)
        row[:3] = (self.uav_positions[i]-(0,0,50))/(1000,1000,100)
        row[-1] = self.current_step/self.max_steps
        return row

    def step(self,actions):
        for i,agent in enumerate(self.agents):
            if agent in actions:
                self.uav_positions[i] = np.clip(self.uav_positions[i]+30*np.asarray(actions[agent]),(0,0,50),(1000,1000,150))
        self._begin_path_loss_step()
        self._update_channel_state()
        self.current_step += 1
        return ({agent:self._get_observation(agent) for agent in self.agents},
                {agent:0. for agent in self.agents},
                {agent:self.current_step>=self.max_steps for agent in self.agents},
                {agent:False for agent in self.agents}, {agent:{} for agent in self.agents})

    base = e.MultiUAVEnv
    for name,function in (('__init__',initialize),('reset',reset),('step',step),('_begin_path_loss_step',begin),
            ('_update_channel_state',update),('_get_observation',observation)):
        monkeypatch.setattr(base,name,function)
    monkeypatch.setattr(base,'_compute_path_loss_matrix',lambda self:np.full((5,50),80.,np.float64))
    def air_loss(self):
        result = np.full((5,5),90.,np.float64)
        np.fill_diagonal(result,0.)
        return result
    monkeypatch.setattr(base,'_compute_uav_path_loss_matrix',air_loss)
    monkeypatch.setattr(base,'_path_loss_matrices_are_current',lambda self:self._ready)
    monkeypatch.setattr(base,'_vector_channel_state_is_current',lambda self:self._ready)
    monkeypatch.setattr(base,'_cached_uav_user_path_loss',lambda self,i,j:self._uav_user_path_loss_matrix[i,j])
    return calls,normals


def actions(env,value=(0.,0.,0.)):
    return {agent:np.array(value) for agent in env.agents}


def test_constructor_and_resets_preserve_outputs_world_tick_and_monotone_counts(doubled_native):
    calls,_ = doubled_native
    env = e.CorrelatedShadowEnv(c.FIXTURE_CONSTRUCTOR_SEEDS[0],horizon=8)
    assert calls == [(c.FIXTURE_CONSTRUCTOR_SEEDS[0],0)]
    counts = env.physical_counters
    assert counts['constructor_calls_attempted'] == counts['constructor_calls_completed'] == 1
    assert counts['constructor_reset_calls_attempted'] == counts['constructor_reset_calls_completed'] == 1
    assert counts['explicit_reset_calls_attempted'] == 0
    snapshot = env.physical_snapshot()
    assert_host_snapshot(snapshot)
    initial_eps = np.arange(250,dtype=np.float64).reshape(5,50)/1000+c.FIXTURE_CONSTRUCTOR_SEEDS[0]%10
    np.testing.assert_array_equal(snapshot['residual'],c.SIGMA_DB*initial_eps)
    initial = env.constructor_reset_output
    assert set(initial[0]) == set(env.agents) and all(row.shape == (104,) for row in initial[0].values())
    initial[0]['uav_0'].fill(99)
    assert not np.all(env.constructor_reset_output[0]['uav_0'] == 99)
    result = env.reset(seed=c.FIXTURE_SEED)
    assert all(row.dtype == np.float32 for row in result[0].values())
    assert calls[-1] == (c.FIXTURE_SEED,0)
    assert env.physical_snapshot()['world'] == c.FIXTURE_SEED and env.physical_snapshot()['tick'] == 0
    env.step(actions(env))
    env.reset()
    assert calls[-1] == (c.FIXTURE_SEED,0) and env.current_step == 0
    counts = env.physical_counters
    assert counts['explicit_reset_calls_attempted'] == counts['explicit_reset_calls_completed'] == 2
    assert counts['physical_initializations'] == 3 and counts['physical_updates'] == 1
    assert counts['physical_normal_blocks_attempted'] == counts['physical_normal_blocks_completed'] == 4
    assert counts['physical_normal_values_completed'] == counts['physical_normal_values_attempted'] == 1000


@pytest.mark.parametrize('sigma',[0.,c.SIGMA_DB])
def test_clipped_three_dimensional_displacement_hover_and_silent_links(doubled_native,sigma):
    calls,_ = doubled_native
    env = e.CorrelatedShadowEnv(c.FIXTURE_SEED,horizon=8,sigma=sigma)
    before = env.physical_snapshot()
    env.set_transmitter_mask(np.zeros(5,bool))
    command = actions(env)
    command['uav_0'] = np.array([1.,-1.,1.])  # Full clipping: actual displacement is0.
    command['uav_1'] = np.array([1.,0.,0.])
    command['uav_2'] = np.array([1.,1.,-1.])
    geometry_rng = env.np_random
    env.step(command)
    after = env.physical_snapshot()
    delta = after['positions']-before['positions']
    rho = np.exp(-np.sqrt(np.square(delta).sum(axis=1))/c.CORRELATION_METRES)[:,None]
    eps = np.arange(250,dtype=np.float64).reshape(5,50)/1000+1+c.FIXTURE_SEED%10
    expected = rho*before['residual'] + sigma*np.sqrt(1.-np.square(rho))*eps
    np.testing.assert_allclose(after['residual'],expected,rtol=1e-14,atol=1e-14)
    np.testing.assert_array_equal(after['residual'][0],before['residual'][0])
    np.testing.assert_array_equal(after['residual'][3:],before['residual'][3:])
    assert calls == [(c.FIXTURE_SEED,0),(c.FIXTURE_SEED,1)]
    assert after['tick'] == env.current_step == 1 and after['counters']['physical_normal_values_completed'] == 500
    assert env.np_random is geometry_rng and np.isneginf(after['sinr']).all()
    np.testing.assert_array_equal(after['user_loss'],80.+after['residual'])
    if sigma == 0:
        assert not after['residual'].any()
        np.testing.assert_array_equal(after['user_loss'],np.full((5,50),80.))


def test_getters_mask_and_recomputation_never_consume_noise_or_advance_residual(doubled_native):
    calls,_ = doubled_native
    env = e.CorrelatedShadowEnv(c.FIXTURE_SEED,horizon=8)
    before = env.physical_snapshot()
    geometry_rng = env.np_random
    for agent in env.agents:
        env._get_observation(agent)
    env.set_transmitter_mask(np.array([True,False,True,False,False]))
    env._compute_path_loss_matrix()
    env._compute_uav_path_loss_matrix()
    env._compute_path_loss(env.uav_positions[1],7)
    env._compute_path_loss(env.uav_positions[2],env.user_positions[8])
    env._update_channel_state()
    env._begin_path_loss_step()  # Cache refresh only, never an implicit new physical tick.
    with pytest.raises(RuntimeError,match='existing current native channel'):
        env.physical_snapshot()
    env._update_channel_state()
    after = env.physical_snapshot()
    assert calls == [(c.FIXTURE_SEED,0)] and env.np_random is geometry_rng
    assert after['counters'] == before['counters'] and after['tick'] == before['tick']
    np.testing.assert_array_equal(after['residual'],before['residual'])
    np.testing.assert_array_equal(env._uav_uav_path_loss_matrix,np.full((5,5),90.)-np.eye(5)*90.)
    assert_host_snapshot(after)


def test_snapshots_and_public_counters_have_no_mutable_aliases(doubled_native):
    env = e.CorrelatedShadowEnv(c.FIXTURE_SEED,horizon=8)
    before = env.physical_snapshot()
    altered = env.physical_snapshot()
    for value in altered.values():
        if isinstance(value,np.ndarray): value.fill(0)
    altered['counters'].clear()
    env.physical_counters.clear()
    after = env.physical_snapshot()
    for key,value in before.items():
        if isinstance(value,np.ndarray): np.testing.assert_array_equal(after[key],value)
        else: assert after[key] == value


@pytest.mark.parametrize('field',['positions','users','clock','configuration'])
def test_unsupported_external_mutation_fails_before_any_extra_noise(doubled_native,field):
    calls,_ = doubled_native
    env = e.CorrelatedShadowEnv(c.FIXTURE_SEED,horizon=8)
    if field == 'positions': env.uav_positions[0,0] -= 1
    if field == 'users': env.user_positions[0,0] += 1
    if field == 'clock': env.current_step += 1
    if field == 'configuration': env.max_speed += 1
    for function in (lambda:env._get_observation('uav_0'),env.physical_snapshot,
                     lambda:env.set_transmitter_mask(np.ones(5,bool)),lambda:env.step(actions(env))):
        with pytest.raises(RuntimeError): function()
    assert calls == [(c.FIXTURE_SEED,0)]
    assert env.physical_counters['physical_normal_values_completed'] == 250


def test_failure_counters_distinguish_attempts_and_returned_calls(doubled_native,monkeypatch):
    env = e.CorrelatedShadowEnv(c.FIXTURE_SEED,horizon=8)
    def failed(*args): raise ArithmeticError('synthetic normal failure')
    monkeypatch.setattr(e,'physical_normals',failed)
    with pytest.raises(ArithmeticError): env.step(actions(env,(1.,0.,0.)))
    counts = env.physical_counters
    assert counts['native_step_calls_attempted'] == 1 and counts['native_step_calls_completed'] == 0
    assert counts['physical_normal_blocks_attempted'] == 2 and counts['physical_normal_blocks_completed'] == 1
    assert counts['physical_normal_values_attempted'] == 500 and counts['physical_normal_values_completed'] == 250
    assert counts['physical_updates'] == 0


@pytest.mark.parametrize('kwargs',[{'seed':-1},{'seed':True},{'seed':2**32},{'seed':c.FIXTURE_SEED,'horizon':9},
                                  {'seed':c.FIXTURE_SEED,'sigma':-1.},{'seed':c.FIXTURE_SEED,'sigma':np.nan}])
def test_invalid_construction_never_reaches_native_constructor(doubled_native,kwargs):
    calls,_ = doubled_native
    with pytest.raises(ValueError): e.CorrelatedShadowEnv(**kwargs)
    assert calls == []


def test_make_env_uses_existing_adapter_without_an_extra_reset(monkeypatch):
    calls = []
    base = object()
    adapter = object()
    def constructor(seed,*,horizon,sigma):
        calls.append(('base',seed,horizon,sigma))
        return base
    def wrap(value,*,seed):
        assert value is base
        calls.append(('adapter',seed))
        return adapter
    monkeypatch.setattr(e,'CorrelatedShadowEnv',constructor)
    monkeypatch.setattr(e,'ParallelToArrayAdapter',wrap)
    assert e.make_env(c.FIXTURE_SEED,horizon=8,sigma=0.) is adapter
    assert calls == [('base',c.FIXTURE_SEED,8,0.),('adapter',c.FIXTURE_SEED)]
