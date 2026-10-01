"""One full saved-data replay: scalar physics and independent policy laws."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from .contract import FITTED, NEURAL, array_digest
from .environment import original_layout
from .physics import assert_radio_equal, scalar_state
from .reading import episode_metrics


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def equal(actual, expected, message, tolerance=None):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape, message + ': shape')
    if tolerance is None:
        require(np.array_equal(a, b), message)
    else:
        require(np.isfinite(a).all() and np.isfinite(b).all()
                and np.allclose(a, b, atol=tolerance, rtol=0.), message)


def _gate_vector(answer, kind):
    features = np.asarray(answer['features'])
    count = min(sum(float(features[3 + 3 * i + 2]) > 0 for i in range(20)), 10)
    onehot = np.array([float(i == count) for i in range(11)], dtype=np.float64)
    raw = np.r_[features.astype(np.float64), onehot]
    return (raw if kind == 'RAW' else np.r_[raw, answer['hidden'].astype(np.float64)]), count


def _schema(raw, horizon, parent):
    d = horizon // 4
    shapes = dict(positions=(horizon + 1, 5, 3), observations=(horizon, 5, 104), commands=(horizon, 5, 3),
                  reward=(horizon,), served=(horizon,), sinr_quality=(horizon,), sinr=(horizon, 5, 50),
                  peer_sinr=(horizon, 5, 5), connections=(horizon, 5, 50), transmitter_mask=(horizon, 5),
                  terminated=(horizon,), truncated=(horizon,), step_generation=(horizon,), step_path_loss_misses=(horizon,),
                  nav_pre=(d, 5), nav_next=(d, 5), fallback=(d, 5), action_index=(d, 5), memo_hit=(d, 5),
                  features=(d, 5, 114), n_current=(d, 5), n_peers=(d, 5), probabilities=(d, 5, 27),
                  innovation=(d, 5), entropy=(d, 5), old_decision_mask=(d, 5), installed_mask=(d, 5),
                  refresh_sinr=(d, 5, 50), refresh_peer_sinr=(d, 5, 5), refresh_connections=(d, 5, 50),
                  refresh_observations=(d, 5, 104), initial_users=(50, 2), initial_sinr=(5, 50),
                  initial_peer_sinr=(5, 5), initial_connections=(5, 50), initial_generation=(),
                  terminal_observation=(5, 104), decision_ticks=(d,))
    for key in ('eligible_agent', 'gate_count', 'gate_innovation', 'gate_prediction', 'gate_requested_off',
                'gate_off', 'gate_forced', 'refresh_generation', 'refresh_path_loss_misses'):
        shapes[key] = (d,)
    if parent in NEURAL:
        shapes.update(logits=(d, 5, 27), hidden=(d, 5, 128))
    if parent not in ('P0', 'Bstar0'):
        shapes.update(policy_scores=(d, 5, 27), policy_served=(d, 5, 27), c_index=(d, 5))
    if parent == 'Hdirect':
        shapes['parent_probabilities'] = (d, 5, 27)
    require(set(raw) == set(shapes), 'complete raw field roster')
    booleans = {'connections', 'transmitter_mask', 'terminated', 'truncated', 'fallback', 'memo_hit',
                'old_decision_mask', 'installed_mask', 'gate_requested_off', 'gate_off', 'gate_forced',
                'refresh_connections', 'initial_connections'}
    integers = {'served', 'step_generation', 'step_path_loss_misses', 'nav_pre', 'nav_next', 'action_index',
                'n_current', 'n_peers', 'eligible_agent', 'gate_count', 'refresh_generation', 'refresh_path_loss_misses',
                'initial_generation', 'decision_ticks', 'c_index'}
    fp32 = {'observations', 'commands', 'features', 'refresh_observations', 'terminal_observation', 'logits', 'hidden'}
    for key, shape in shapes.items():
        value = raw[key]
        require(value.shape == shape, key + ': raw shape')
        expected_dtype = np.bool_ if key in booleans else np.int64 if key in integers else np.float32 if key in fp32 else np.float64
        require(value.dtype == expected_dtype, key + ': raw dtype')
        if 'sinr' not in key or key == 'sinr_quality':
            require(np.isfinite(value).all(), key + ': nonfinite value')
    equal(raw['decision_ticks'], np.arange(0, horizon, 4), 'complete decision clocks')


def _radio(raw, prefix, index, state, maxima):
    for key in ('sinr', 'peer_sinr'):
        stored = raw[prefix + key] if index is None else raw[prefix + key][index]
        maxima['radio'] = max(maxima['radio'], assert_radio_equal(stored, state[key]))
    stored = raw[prefix + 'connections'] if index is None else raw[prefix + 'connections'][index]
    equal(stored, state['connections'], prefix + 'greedy capacity assignment')


def audit_episode(raw, row, protocol, actor, *, params=None, counts=None, inflight=None):
    # Importing the reference here lets scalar-only tests avoid loading torch.
    from .reference import ReferencePolicy
    counts = {} if counts is None else counts
    parent, gate = row['program'].split('_', 1)
    _schema(raw, protocol.horizon, parent)
    world, horizon = row['world'], protocol.horizon
    positions, users = original_layout(world)
    equal(raw['positions'][0], positions, 'original five-agent reset positions')
    equal(raw['initial_users'], users, 'original user reset positions')
    require(row['initial_state_sha256'] == array_digest(positions, users), 'initial state digest')
    initial_generation = int(raw['initial_generation'])
    equal(raw['step_generation'], initial_generation + np.arange(1, horizon + 1), 'one physical generation per native tick')
    equal(raw['refresh_generation'], initial_generation + np.arange(0, horizon, 4), 'setter reuses physical generation')
    equal(raw['step_path_loss_misses'], np.full(horizon, 260), 'native vector cache-miss slot counter')
    equal(raw['refresh_path_loss_misses'], np.zeros(horizon // 4, dtype=int), 'no setter distance recomputation')
    equal(raw['terminated'], np.arange(horizon) == horizon - 1, 'terminal clock')
    equal(raw['truncated'], np.zeros(horizon, dtype=bool), 'no truncation')
    maxima = dict(radio=0., observation=0., reward=0., prediction=0.)
    mask = np.ones(5, dtype=bool)
    state = scalar_state(positions, users, mask, 0, horizon, counts=counts)
    _radio(raw, 'initial_', None, state, maxima)
    navs = [initial_nav(raw['observations'][0, agent]) for agent in range(5)]
    policies = [ReferencePolicy(parent, actor, world=world, agent=agent, sampling_root=row['motion_root']) for agent in range(5)]
    if inflight is not None:
        inflight.update(id=row['id'], parent=parent, policy_agents=[policy.counters for policy in policies])
    forced_features = None
    for tick in range(horizon):
        if inflight is not None:
            inflight['tick'] = tick
        equal(raw['observations'][tick], state['observations'], 'saved old returned observation', tolerance=1e-7)
        maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(raw['observations'][tick] - state['observations']))))
        if tick % 4 == 0:
            di, agent = tick // 4, (tick // 4) % 5
            equal(raw['old_decision_mask'][di], mask, 'decision uses previous applied mask')
            equal(raw['nav_pre'][di], navs, 'private navigation recurrence')
            equal(raw['eligible_agent'][di], agent, 'rotating eligibility')
            answers = []
            for i, policy in enumerate(policies):
                answer = policy.query(raw['observations'][tick, i].copy(), tick, int(navs[i]))
                answers.append(answer)
                navs[i] = answer['next_nav']
                for field in ('features', 'fallback', 'action_index', 'memo_hit', 'n_current', 'n_peers', 'innovation'):
                    equal(raw[field][di, i], answer[field], 'motion ' + field)
                for field in ('probabilities', 'entropy'):
                    equal(raw[field][di, i], answer[field], 'motion ' + field, tolerance=5e-14)
                if parent in NEURAL:
                    for field in ('logits', 'hidden'):
                        equal(raw[field][di, i], answer[field], 'original paid forward ' + field)
                if parent not in ('P0', 'Bstar0'):
                    equal(raw['policy_scores'][di, i], answer['scores'], 'complete C scores', tolerance=1e-12)
                    equal(raw['policy_served'][di, i], answer['served'], 'complete C service')
                    equal(raw['c_index'][di, i], answer['c_index'], 'C anchor')
                if parent == 'Hdirect':
                    equal(raw['parent_probabilities'][di, i], answer['parent_probabilities'], 'H parent law', tolerance=5e-14)
                expected_command = COMMANDS[answer['action_index']]
                equal(raw['commands'][tick:tick + 4, i], np.tile(expected_command, (4, 1)), 'four held original motion commands')
            equal(raw['nav_next'][di], navs, 'navigation update')
            vector, count = _gate_vector(answers[agent], 'HIDDEN' if gate == 'HIDDEN' else 'RAW')
            prediction, uniform = 0., -1.
            if gate in FITTED:
                require(params is not None, 'fitted gate coefficients')
                prediction = float(((vector - params['mean']) / params['scale']) @ params['coefficients'] + params['intercept'])
                requested = prediction > 0.
            elif gate == 'R':
                uniform = float(np.random.default_rng(np.random.SeedSequence([row['gate_root'], world, tick, agent])).random())
                requested = uniform < .5
            elif gate == 'ZERO':
                requested = count == 0
            else:
                require(gate in ('A', 'O'), 'declared fixed gate')
                requested = gate == 'O'
            forced = row['kind'] == 'acquisition' and tick == row['force_tick']
            executed = (row['branch'] == 'OFF') if forced else requested
            for key, value in (('gate_count', count), ('gate_innovation', uniform), ('gate_requested_off', requested),
                               ('gate_off', executed), ('gate_forced', forced)):
                equal(raw[key][di], value, 'gate law ' + key)
            equal(raw['gate_prediction'][di], prediction, 'gate law prediction', tolerance=1e-13)
            maxima['prediction'] = max(maxima['prediction'], abs(float(raw['gate_prediction'][di]) - prediction))
            # Require both the independently computed and stored prediction to
            # imply the same discrete action even arbitrarily close to zero.
            if gate in FITTED:
                require((raw['gate_prediction'][di] > 0.) == executed, 'prediction sign/action consistency')
            if forced:
                forced_features = {name: _gate_vector(answers[agent], name)[0] for name in FITTED}
            mask = np.ones(5, dtype=bool)
            mask[agent] = not executed
            equal(raw['installed_mask'][di], mask, 'one eligible gate bit')
            refreshed = scalar_state(positions, users, mask, tick, horizon, counts=counts)
            _radio(raw, 'refresh_', di, refreshed, maxima)
            equal(raw['refresh_observations'][di], refreshed['observations'], 'saved setter row', tolerance=1e-7)
            maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(
                raw['refresh_observations'][di] - refreshed['observations']))))
        equal(raw['transmitter_mask'][tick], mask, 'four held mask ticks')
        positions = np.clip(positions + raw['commands'][tick].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        equal(raw['positions'][tick + 1], positions, 'held native motion including silent UAVs')
        state = scalar_state(positions, users, mask, tick + 1, horizon, counts=counts)
        _radio(raw, '', tick, state, maxima)
        equal(raw['served'][tick], state['served'], 'native total served')
        for key in ('reward', 'sinr_quality'):
            equal(raw[key][tick], state[key], 'native ' + key, tolerance=2e-13)
            maxima['reward'] = max(maxima['reward'], abs(float(raw[key][tick]) - state[key]))
    equal(raw['terminal_observation'], state['observations'], 'terminal local rows', tolerance=1e-7)
    maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(
        raw['terminal_observation'] - state['observations']))))
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, 'episode metric ' + key, tolerance=1e-12 if type(value) is float else None)
    policy_counts = sum_counts(policy.counters for policy in policies)
    require(policy_counts == row['policy_counts'], 'complete original policy/cache/work counts')
    counts['saved_episodes'] = counts.get('saved_episodes', 0) + 1
    counts['saved_native_ticks'] = counts.get('saved_native_ticks', 0) + horizon
    counts['policy_requests'] = counts.get('policy_requests', 0) + horizon // 4 * 5
    counts['gate_requests'] = counts.get('gate_requests', 0) + horizon // 4
    if inflight is not None:
        inflight.clear()
    return dict(max_abs_errors=maxima, policy_counts=policy_counts), forced_features


def audit_pair(off, on, off_row, on_row, protocol, features_off=None, features_on=None):
    force = off_row['force_tick']
    require(off_row['world'] == on_row['world'] and on_row['force_tick'] == force
            and (off_row['branch'], on_row['branch']) == ('OFF', 'ON'), 'paired branch identity')
    index = protocol.training_worlds.index(off_row['world'])
    require(force == protocol.force_tick(index), 'balanced assigned force clock')
    for key in ('initial_users', 'initial_sinr', 'initial_peer_sinr', 'initial_connections'):
        equal(off[key], on[key], 'common pair ' + key)
    equal(off['positions'][:force + 1], on['positions'][:force + 1], 'complete pre-force positions')
    equal(off['observations'][:force + 1], on['observations'][:force + 1], 'complete pre-force rows')
    for key in ('reward', 'served', 'sinr_quality', 'sinr', 'peer_sinr', 'connections', 'transmitter_mask'):
        equal(off[key][:force], on[key][:force], 'complete scored prefix ' + key)
    d = force // 4
    for key in ('nav_pre', 'nav_next', 'fallback', 'action_index', 'memo_hit', 'features', 'n_current', 'n_peers',
                'probabilities', 'innovation', 'entropy', 'logits', 'hidden', 'old_decision_mask', 'gate_count',
                'gate_innovation', 'gate_prediction', 'gate_requested_off', 'gate_forced'):
        equal(off[key][:d + 1], on[key][:d + 1], 'common forced decision ' + key)
    equal(off['commands'][:force + 4], on['commands'][:force + 4], 'common forced-boundary motion')
    for raw, branch in ((off, True), (on, False)):
        require(bool(raw['gate_off'][d]) == branch and np.count_nonzero(raw['gate_forced']) == 1,
                'one forced decision with opposite executed bits')
    agent = d % 5
    saved = {}
    for kind in FITTED:
        saved[kind] = _gate_vector(dict(features=off['features'][d, agent], hidden=off['hidden'][d, agent]), kind)[0]
        if features_off is not None:
            equal(features_off[kind], saved[kind], 'returned forced features')
            equal(features_on[kind], saved[kind], 'common independently reconstructed features')
    target = float(off['reward'].mean() - on['reward'].mean())
    equal(target, off_row['J'] - on_row['J'], 'full episode OFF minus ON label')
    return saved, target
