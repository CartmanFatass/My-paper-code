"""Independent saved-policy replay, native formulas and baseline provenance."""
import numpy as np
import torch
from torch.nn import functional as F

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS, analyze
from experiments.candidates.uav_fleet_adaptation.b02.read import check_memo
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, own_position, require
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_local import (
    _schema, _native, _bundle, _decode, verify_local as verify_ordinary,
)
from .contract import arm_parts


def _forward(actor, features, head):
    """Reconstruct the pinned linear/ReLU path and bounded head algebra directly."""
    x = torch.from_numpy(features.copy()).reshape(1, 114)
    with torch.inference_mode():
        x = torch.relu(F.linear(x, actor.network[0].weight, actor.network[0].bias))
        h = torch.relu(F.linear(x, actor.network[2].weight, actor.network[2].bias))[0]
        # Preserve the original one-row matrix linear operation for the last layer.
        z = F.linear(h.reshape(1, 128), actor.network[4].weight, actor.network[4].bias)[0]
        if head is None:
            logits = z
        elif head.kind == 'CAL':
            logits = z + .5 * torch.tanh(head.alpha * (z - z.mean()) + head.b)
        else:
            logits = z + .5 * torch.tanh(torch.mv(head.W, h) + head.b)
    return h.numpy().copy(), z.numpy().copy(), logits.numpy().copy()


def verify_local(raw, row, protocol, actor, head, bundle, calls, check):
    program, _ = arm_parts(row['arm'])
    if program in ('C', 'Q_I'):
        require(head is None, 'ordinary policy has a head')
        return verify_ordinary(raw, row, protocol, actor, bundle, calls, check)
    h, d = protocol.horizon, protocol.horizon // 4
    require(row['tape'] in protocol.tapes and actor is not None, 'learned row identity')
    require((head is not None) == (program in ('CAL', 'CONT', 'CAL_all', 'CONT_all')), 'head/program mismatch')
    require(row['temperature'] == (2. if program == 'Bstar' else 1.), 'fixed temperature identity')
    _schema(raw, h, True, True)
    for key, shape, dtype in (('hidden', (d, 5, 128), np.float32),
                              ('base_logits', (d, 5, 27), np.float32), ('logp', (d, 5), np.float64)):
        require(raw[key].shape == shape and raw[key].dtype == dtype and np.isfinite(raw[key]).all(),
                'immutable learned array ' + key)
    audit = _native(raw, row, h, calls, check)
    _bundle(raw, row, bundle, d, True)
    obs = raw['observations'][::4]
    equal(raw['features'][..., :103], obs[..., :103], 'actor local103 provenance')
    equal(raw['features'][..., 103:113], np.eye(10, dtype=np.float32)[raw['nav_pre']], 'own nav feature')
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
    equal(raw['proposals'], COMMANDS[raw['action_index']], 'pre-S2 proposal identity')
    expected = check_memo({**raw, 'action_index': raw['modal_index']}, {**row, 'arm': 'S_greedy'}, '', 'student')
    expected['cache_array_bytes'] += expected['misses'] * (128 * 4 + (27 * 4 if head is not None else 0))
    expected['head_rows'] = expected['misses'] if head is not None else 0
    require(row['policy_counts'] == expected, 'policy/private-cache work accounting')
    for j in range(d):
        for agent in range(5):
            check()
            n, peers = int(raw['n_current'][j, agent]), int(raw['n_peers'][j, agent])
            calls['S_helper_attempts'] += 1
            calls['S_helper_setup_links_attempts'] += (1 + peers) * n
            calls['S_helper_extreme_links_attempts'] += 2 * n
            helper = analyze(obs[j, agent].copy(), int(raw['nav_pre'][j, agent]))
            calls['S_helper_completed'] += 1
            calls['S_helper_setup_links_completed'] += helper['counters']['helper_setup_links']
            calls['S_helper_extreme_links_completed'] += helper['counters']['helper_extreme_links']
            equal(helper['features'], raw['features'][j, agent], 'helper features')
            for saved, value in (('fallback', helper['fallback']), ('nav_next', helper['next_nav']),
                                 ('n_current', helper['n_current']), ('n_peers', helper['n_peers'])):
                require(raw[saved][j, agent] == value, 'helper ' + saved)
            require(helper['counters']['helper_calls'] == 1
                    and helper['counters']['helper_setup_links'] == (1 + peers) * n
                    and helper['counters']['helper_extreme_links'] == 2 * n, 'helper work')
            check()
            calls['S_forward_attempts'] += 1
            head_kind = ('new_head' if program in ('CAL', 'CONT') else 'transfer_head') if head is not None else None
            if head_kind is not None:
                calls[head_kind + '_attempts'] += 1
            hidden, base, logits = _forward(actor, helper['features'], head)
            calls['S_forward_completed'] += 1
            if head_kind is not None:
                calls[head_kind + '_completed'] += 1
            equal(raw['hidden'][j, agent], hidden, 'frozen hidden cache identity')
            equal(raw['base_logits'][j, agent], base, 'frozen base-logit cache identity')
            equal(raw['logits'][j, agent], logits, 'bounded head logits')
            scaled = logits.astype(np.float64) / row['temperature']
            p = np.exp(scaled - float(scaled.max()))
            p /= p.sum(dtype=np.float64)
            if program == 'Bstar':
                calls['bstar_applications'] += 1
            equal(raw['probabilities'][j, agent], p, 'nominal FP64 local law')
            require(int(raw['modal_index'][j, agent]) == int(np.argmax(p)), 'modal tie order')
            _decode(raw, j, agent, p, bundle)
            chosen = float(p[int(raw['action_index'][j, agent])])
            equal(raw['logp'][j, agent], np.log(chosen), 'nominal proposal log density')
    audit.update(arm=row['arm'], world=row['world'], tape=row['tape'], expected_policy_counts=expected,
                 S_recomputed_rows=d * 5, head_recomputed_rows=d * 5 if head is not None else 0,
                 sampled_pre_S2_proposals=d * 5)
    return audit


def verify_critic_inputs(raw, row, protocol, calls):
    """Derive pre-query baseline data from saved native coordinates/deliveries.

    No critic forward or optimizer replay is performed by the result reader.
    """
    d = protocol.horizon // 4
    if row['phase'] != 'training':
        require(not any(key.startswith('critic_') for key in raw) and 'values' not in raw,
                'deployed final policy acquired training-only critic information')
        return
    for key, shape, dtype in (('critic_states', (d, 116), np.float32),
                              ('critic_features', (d, 186), np.float32),
                              ('critic_actual', (d, 5, 3), np.float32), ('critic_mask', (d, 5), bool),
                              ('critic_nav', (d, 5), np.int64), ('values', (d,), np.float32),
                              ('macro_rewards', (d,), np.float64)):
        require(raw[key].shape == shape and raw[key].dtype == dtype and np.isfinite(raw[key]).all(),
                'critic/target schema ' + key)
    for j, tick in enumerate(range(0, protocol.horizon, 4)):
        native = np.concatenate((raw['positions'][tick].reshape(-1), raw['initial_users'].reshape(-1),
                                 [tick / protocol.horizon])).astype(np.float32)
        equal(raw['critic_states'][j], native, 'pre-query native critic state')
        actual = np.zeros((5, 3), np.float32) if tick == 0 else raw['commands'][tick - 1]
        mask = np.ones(5, bool) if tick == 0 else raw['transmitter_mask'][tick - 1]
        equal(raw['critic_actual'][j], actual, 'baseline prior delivered commands; startup zero')
        equal(raw['critic_mask'][j], mask, 'baseline prior delivered radio mask')
        equal(raw['critic_nav'][j], raw['nav_pre'][j], 'baseline before query/nav advance')
        # Independent explicit normalization; no candidate critic_features call.
        xyz = native[:15].reshape(5, 3).copy()
        xyz[:, :2] = xyz[:, :2] / np.float32(1000.)
        xyz[:, 2] = (xyz[:, 2] - np.float32(50.)) / np.float32(100.)
        state = np.concatenate((xyz.reshape(-1), native[15:115] / np.float32(1000.), native[-1:]))
        features = np.concatenate((state, actual.reshape(-1), mask.astype(np.float32),
                                   np.eye(10, dtype=np.float32)[raw['nav_pre'][j]].reshape(-1)))
        equal(raw['critic_features'][j], features, '186-input finite pre-action baseline')
    equal(raw['macro_rewards'], raw['reward'].reshape(d, 4).sum(axis=1, dtype=np.float64), 'native macro rewards')
    calls['critic_input_rows'] += d
