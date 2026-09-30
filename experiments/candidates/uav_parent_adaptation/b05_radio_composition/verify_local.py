"""Bounded saved native/local-policy reconstruction; never creates a host."""

import math

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS, analyze
from experiments.candidates.uav_fleet_adaptation.b02.read import check_memo, saved_ranking_choice
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, own_position, require
from experiments.candidates.uav_radio_activation.b01.read import observed_rows, radio

from .contract import arm_parts


M = 1 << 53


def local_counts():
    return dict(actual_motion_agent_ticks=0, native_formula_attempts=0, native_formula_completed=0,
                native_user_links_attempts=0, native_user_links_completed=0,
                native_peer_geometry_links_attempts=0, native_peer_geometry_links_completed=0,
                S_helper_attempts=0, S_helper_completed=0,
                S_helper_setup_links_attempts=0, S_helper_setup_links_completed=0,
                S_helper_extreme_links_attempts=0, S_helper_extreme_links_completed=0,
                S_forward_attempts=0, S_forward_completed=0, C_fallback_candidate_motion_steps=0)


def _schema(raw, h, student, stochastic):
    d = h // 4
    fields = dict(
        observations=((h, 5, 104), np.float32), positions=((h + 1, 5, 3), np.float64),
        commands=((h, 5, 3), np.float32), proposals=((d, 5, 3), np.float32),
        transmitter_mask=((h, 5), bool), terminal_mask=((5,), bool),
        reward=((h,), np.float64), served=((h,), np.int16), sinr_quality=((h,), np.float64),
        sinr=((h, 5, 50), np.float64), connections=((h, 5, 50), bool),
        decision_ticks=((d,), np.int64), initial_users=((50, 2), np.float64),
        terminal_observation=((5, 104), np.float32), features=((d, 5, 114), np.float32),
        nav_pre=((d, 5), np.int64), nav_next=((d, 5), np.int64), fallback=((d, 5), bool),
        memo_hit=((d, 5), bool), n_current=((d, 5), np.int64), n_peers=((d, 5), np.int64),
        action_index=((d, 5), np.int64), modal_index=((d, 5), np.int64),
        probabilities=((d, 5, 27), np.float64), completed_steps=((), np.int64),
        completed_decisions=((), np.int64), episode_complete=((), bool))
    if student:
        fields['logits'] = ((d, 5, 27), np.float32)
    else:
        fields.update(policy_scores=((d, 5, 27), np.float64), policy_served=((d, 5, 27), np.float64))
    if stochastic:
        fields.update(departure_threshold=((d, 5), np.int64),
                      tail_thresholds=((d, 5, 26), np.uint64),
                      effective_probabilities=((d, 5, 27), np.float64),
                      departure_integer=((d, 5), np.int64), requested_departure=((d, 5), bool),
                      private_depart_integer=((d, 5), np.uint64), private_tail_integer=((d, 5), np.uint64))
    for key, (shape, dtype) in fields.items():
        require(key in raw and isinstance(raw[key], np.ndarray), 'missing local/native array ' + key)
        require(raw[key].shape == shape and raw[key].dtype == dtype, 'local/native shape or dtype ' + key)
        if key != 'sinr':
            require(np.isfinite(raw[key]).all(), 'nonfinite local/native ' + key)
    require(bool(raw['episode_complete']) and int(raw['completed_steps']) == h
            and int(raw['completed_decisions']) == d, 'incomplete local/native endpoint')
    equal(raw['decision_ticks'], np.arange(0, h, 4), 'local decision clock')
    for key, upper in (('nav_pre', 10), ('nav_next', 10), ('action_index', 27), ('modal_index', 27),
                       ('n_current', 21), ('n_peers', 5)):
        require(np.all((raw[key] >= 0) & (raw[key] < upper)), 'invalid local category ' + key)
    require(np.isfinite(raw['sinr'][raw['transmitter_mask']]).all()
            and np.isneginf(raw['sinr'][~raw['transmitter_mask']]).all(),
            'native SINR must be finite active rows and -inf silent rows only')
    require('public_integer' not in raw, 'unused public stream must not be exposed in local records')


def _mask_integer(mask):
    return sum((1 << i) for i, active in enumerate(mask) if active)


def _formula(positions, users, mask, calls, check, *, tick=None, horizon=None):
    check()
    peers = int(np.count_nonzero(mask))
    geometry = peers * (peers - 1) ** 2 if tick is not None else 0
    calls['native_formula_attempts'] += 1
    calls['native_user_links_attempts'] += 250
    calls['native_peer_geometry_links_attempts'] += geometry
    if tick is None:
        result = radio(positions, users, _mask_integer(mask))
    else:
        result = observed_rows(positions, users, _mask_integer(mask), tick)
        # The pinned reader binds H256. Short synthetic fixtures change only clock units.
        result[:, -1] = tick / horizon
    calls['native_formula_completed'] += 1
    calls['native_user_links_completed'] += 250
    calls['native_peer_geometry_links_completed'] += geometry
    return result


def _native(raw, row, h, calls, check):
    rng = np.random.RandomState(row['world'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                        for _ in range(5)])
    users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
    equal(raw['positions'][0], initial, 'seeded initial positions')
    equal(raw['initial_users'], users, 'seeded initial users')
    require(row['initial_state_sha256'] == array_digest(initial, users), 'initial state digest')
    served = raw['connections'].sum(axis=(1, 2))
    equal(raw['served'], served, 'native served count')
    require(not np.any(raw['connections'].sum(axis=1) > 1)
            and not np.any(raw['connections'].sum(axis=2) > 10), 'native connection capacity')
    require(np.all(raw['sinr'][raw['connections']] >= 3), 'ineligible native connection')
    quality = np.where(raw['connections'], np.clip((raw['sinr'] - 3) / 30, 0, 1), 0).sum(axis=(1, 2))
    quality /= np.maximum(served, 1)
    equal(raw['sinr_quality'], quality, 'native quality reduction', 1e-12)
    equal(raw['reward'], .7 * served / 50 + .3 * quality, 'native reward reduction', 1e-12)
    calls['actual_motion_agent_ticks'] += h * 5
    equal(raw['positions'][1:], np.clip(raw['positions'][:-1] + raw['commands'].astype(np.float64) * 30,
                                      [0, 0, 50], [1000, 1000, 150]), 'actual native motion')
    require(np.all(np.isin(raw['commands'], (-1, 0, 1))), 'invalid actual discrete command')
    scale, offset = np.array([1000, 1000, 100]), np.array([0, 0, 50])
    tolerance = np.finfo(np.float32).eps * scale
    require(np.allclose(raw['observations'][..., :3].astype(np.float64) * scale + offset,
                        raw['positions'][:-1], rtol=0, atol=tolerance), 'observed own coordinates')
    require(np.allclose(raw['terminal_observation'][..., :3].astype(np.float64) * scale + offset,
                        raw['positions'][-1], rtol=0, atol=tolerance), 'terminal own coordinates')
    equal(raw['observations'][..., -1], np.broadcast_to(
        (np.arange(h) / h).astype(np.float32)[:, None], (h, 5)), 'observation clock')
    equal(raw['terminal_observation'][:, -1], np.ones(5, np.float32), 'terminal clock')
    max_sinr, max_metric, max_observation = 0., 0., 0.
    for tick in range(h):
        sinr, connections, metrics = _formula(raw['positions'][tick + 1], users,
                                              raw['transmitter_mask'][tick], calls, check)
        equal(raw['sinr'][tick], sinr, 'actual-mask native SINR', 1e-9)
        equal(raw['connections'][tick], connections, 'actual-mask native connections')
        actual = np.array([raw['reward'][tick], raw['served'][tick], raw['sinr_quality'][tick]])
        expected = np.array([metrics['J'], metrics['served'], metrics['quality']])
        equal(actual, expected, 'actual-mask native metrics', 1e-12)
        active = raw['transmitter_mask'][tick]
        if active.any():
            max_sinr = max(max_sinr, float(np.max(np.abs(raw['sinr'][tick, active] - sinr[active]))))
        max_metric = max(max_metric, float(np.max(np.abs(actual - expected))))
    for tick in range(0, h, 4):
        expected = _formula(raw['positions'][tick], users, raw['transmitter_mask'][tick],
                            calls, check, tick=tick, horizon=h)
        equal(raw['observations'][tick], expected, 'actual-mask report observation', 1e-6)
        max_observation = max(max_observation, float(np.max(np.abs(raw['observations'][tick] - expected))))
    terminal = _formula(raw['positions'][-1], users, raw['terminal_mask'], calls, check, tick=h, horizon=h)
    equal(raw['terminal_observation'], terminal, 'actual-mask terminal observation', 1e-6)
    return dict(max_native_sinr_error=max_sinr, max_native_metric_error=max_metric,
                max_report_observation_error=max(max_observation, float(np.max(
                    np.abs(raw['terminal_observation'] - terminal)))))


def _bundle(raw, row, bundle, d, stochastic):
    if not stochastic:
        require(bundle is None and row['bundle_sha256'] is None, 'C must have no tape bundle')
        return
    require(bundle is not None, 'stochastic policy requires regenerated bundle')
    for key, shape in (('public', (d,)), ('private_depart', (d, 5)), ('private_tail', (d, 5))):
        require(key in bundle and bundle[key].shape == shape and bundle[key].dtype == np.uint64
                and np.all(bundle[key] < M), 'invalid regenerated tape ' + key)
    require(row['bundle_sha256'] == array_digest(bundle['public'], bundle['private_depart'], bundle['private_tail']),
            'all-three-stream bundle digest')
    equal(raw['private_depart_integer'], bundle['private_depart'], 'fresh private departure tape')
    equal(raw['private_tail_integer'], bundle['private_tail'], 'fresh private tail tape')


def _decode(raw, j, agent, p, bundle):
    modal = int(np.argmax(p))
    b = min(M, max(0, math.ceil((1 - float(p[modal])) * M)))
    ids = [action for action in range(27) if action != modal]
    if b:
        total = p[ids].sum(dtype=np.float64)
        require(total > 0, 'positive departure without tail mass')
        cdf = np.cumsum(p[ids] / total, dtype=np.float64)
        require(np.isfinite(cdf).all() and np.all(cdf >= 0) and np.all(np.diff(cdf) >= 0)
                and np.all(cdf <= 1 + 64 * np.finfo(float).eps), 'tail CDF roundoff/monotonicity')
        thresholds = [math.ceil(min(1., float(value)) * M) for value in cdf]
        thresholds[-1] = M
    else:
        thresholds = [0] * 25 + [M]
    require(int(raw['departure_threshold'][j, agent]) == b, 'departure threshold')
    equal(raw['tail_thresholds'][j, agent], np.array(thresholds, np.uint64), 'tail integer partition')
    effective, previous = np.zeros(27), 0
    effective[modal] = 1 - b / M
    for action, threshold in zip(ids, thresholds):
        effective[action] = (b / M) * ((threshold - previous) / M)
        previous = threshold
    equal(raw['effective_probabilities'][j, agent], effective, 'finite local marginal')
    integer, tail = int(bundle['private_depart'][j, agent]), int(bundle['private_tail'][j, agent])
    require(int(raw['departure_integer'][j, agent]) == integer, 'I departure/private identity')
    depart = integer < b
    require(bool(raw['requested_departure'][j, agent]) == depart, 'requested departure')
    choice = next(action for action, threshold in zip(ids, thresholds) if tail < threshold) if depart else modal
    require(int(raw['action_index'][j, agent]) == choice, 'I finite-grid action')


def verify_local(raw, row, protocol, actor, bundle, calls, check):
    family, _ = arm_parts(row['arm'])
    student, stochastic = family == 'S_I', family != 'C'
    h, d = protocol.horizon, protocol.horizon // 4
    require((row['tape'] == -1) if not stochastic else row['tape'] in protocol.tapes, 'local tape identity')
    require(not student or actor is not None, 'S verification requires its bound actor')
    _schema(raw, h, student, stochastic)
    audit = _native(raw, row, h, calls, check)
    _bundle(raw, row, bundle, d, stochastic)
    obs = raw['observations'][::4]
    equal(raw['features'][..., :103], obs[..., :103], 'local features')
    equal(raw['features'][..., 103:113], np.eye(10, dtype=np.float32)[raw['nav_pre']], 'own navigation feature')
    equal(raw['features'][..., -1], raw['fallback'], 'fallback feature')
    equal(raw['n_current'], np.count_nonzero(obs[..., 3:63].reshape(d, 5, 20, 3)[..., 2] > 0, axis=-1),
          'actual-mask local users')
    equal(raw['n_peers'], np.count_nonzero(obs[..., 63:103].reshape(d, 5, 10, 4)[..., 3] > 0, axis=-1),
          'actual-mask local peers')
    nav = np.array([np.argmin(np.sum((WAYPOINTS - own_position(r)[:2]) ** 2, axis=1)) for r in obs[0]])
    for j in range(d):
        equal(raw['nav_pre'][j], nav, 'own navigation continuity')
        own = np.array([own_position(r) for r in obs[j]])
        nav = np.where(raw['fallback'][j] & (np.linalg.norm(WAYPOINTS[nav] - own[:, :2], axis=1) <= 60),
                       (nav + 1) % 10, nav)
        equal(raw['nav_next'][j], nav, 'own navigation transition')
    equal(raw['proposals'], COMMANDS[raw['action_index']], 'local proposal command')
    base_raw = {**raw, 'action_index': raw['modal_index']}
    expected_counts = check_memo(base_raw, {**row, 'arm': 'S_greedy' if student else 'C_memo'},
                                 '', 'student' if student else 'C')
    require(row['policy_counts'] == expected_counts, 'actual policy/cache counts')
    if not student:
        equal(np.all(raw['policy_served'] == 0, axis=-1), raw['fallback'], 'paid C fallback')
    for j in range(d):
        for agent in range(5):
            if student:
                n, peers = int(raw['n_current'][j, agent]), int(raw['n_peers'][j, agent])
                check()
                calls['S_helper_attempts'] += 1
                calls['S_helper_setup_links_attempts'] += (1 + peers) * n
                calls['S_helper_extreme_links_attempts'] += 2 * n
                helper = analyze(obs[j, agent].copy(), int(raw['nav_pre'][j, agent]))
                calls['S_helper_completed'] += 1
                calls['S_helper_setup_links_completed'] += helper['counters']['helper_setup_links']
                calls['S_helper_extreme_links_completed'] += helper['counters']['helper_extreme_links']
                equal(helper['features'], raw['features'][j, agent], 'S actual-mask helper features')
                for saved, expected in (('fallback', helper['fallback']), ('nav_next', helper['next_nav']),
                                        ('n_current', helper['n_current']), ('n_peers', helper['n_peers'])):
                    require(raw[saved][j, agent] == expected, 'S helper ' + saved)
                require(helper['counters']['helper_calls'] == 1
                        and helper['counters']['helper_setup_links'] == (1 + peers) * n
                        and helper['counters']['helper_extreme_links'] == 2 * n, 'S helper work')
                check()
                calls['S_forward_attempts'] += 1
                with torch.inference_mode():
                    logits = actor(torch.from_numpy(helper['features'].copy()).reshape(1, 114))[0].cpu().numpy()
                calls['S_forward_completed'] += 1
                require(logits.shape == (27,) and logits.dtype == np.float32 and np.isfinite(logits).all(),
                        'invalid S one-row logits')
                equal(raw['logits'][j, agent], logits, 'S frozen one-row logits')
                p = np.exp(logits.astype(np.float64) - float(np.max(logits)))
                p /= p.sum(dtype=np.float64)
            else:
                modal = int(raw['modal_index'][j, agent])
                if not raw['memo_hit'][j, agent]:
                    check()
                    fallback = bool(raw['fallback'][j, agent])
                    if fallback:
                        calls['C_fallback_candidate_motion_steps'] += 27 * 4
                    choice = saved_ranking_choice(obs[j, agent], int(raw['nav_next'][j, agent]), fallback,
                                                  raw['policy_scores'][j, agent], np.arange(27))
                    require(choice == modal, 'paid C score/fallback modal choice')
                p = np.full(27, .1 / 26 if stochastic else 0., dtype=np.float64)
                p[modal] = .9 if stochastic else 1.
            equal(raw['probabilities'][j, agent], p, 'frozen local probability law')
            require(int(raw['modal_index'][j, agent]) == int(np.argmax(p)), 'modal tie order')
            if stochastic:
                _decode(raw, j, agent, p, bundle)
            else:
                require(raw['action_index'][j, agent] == raw['modal_index'][j, agent], 'C deterministic action')
    requested = raw['action_index'] != raw['modal_index']
    counts = requested.sum(axis=1)
    empty = raw['n_current'] == 0
    audit.update(arm=row['arm'], world=row['world'], tape=row['tape'],
                 categorical_departures=int(requested.sum()),
                 categorical_count_histogram=np.bincount(counts, minlength=6).tolist(),
                 empty_local_rows=int(empty.sum()), fallback_local_rows=int(raw['fallback'].sum()),
                 empty_fallback_local_rows=int(np.count_nonzero(empty & raw['fallback'])),
                 silent_local_rows=int(np.count_nonzero(~raw['transmitter_mask'][::4])),
                 S_recomputed_rows=d * 5 if student else 0,
                 S_recomputed_empty_rows=int(empty.sum()) if student else 0,
                 S_recomputed_fallback_rows=int(raw['fallback'].sum()) if student else 0,
                 expected_policy_counts=expected_counts)
    return audit
