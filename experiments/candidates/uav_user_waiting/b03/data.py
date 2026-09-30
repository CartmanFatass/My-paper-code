"""Causal pre-C rows and observed actual M-suffix maximum increments."""
from pathlib import Path

import numpy as np

from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_registered_service.b01.read import load_episode
from experiments.candidates.uav_radio_activation.b01.study import file_identity
from .features import pack_features, FEATURE_DIM


def contact_states(contacts):
    """Boundary arrays include initial0; maximum is updated after each service."""
    contacts = np.asarray(contacts, bool)
    last = np.full(50, -1, np.int64)
    maxima = np.zeros((len(contacts) + 1, 50), np.int64)
    lasts = np.empty_like(maxima)
    lasts[0] = last
    windows = np.zeros((len(contacts) + 1, 4, 50), bool)
    for tick, served in enumerate(contacts):
        last[served] = tick
        lasts[tick + 1] = last
        maxima[tick + 1] = np.maximum(maxima[tick], tick - last)
        windows[tick + 1] = windows[tick]
        windows[tick + 1, tick // 64] |= served
    return lasts, maxima, windows


def episode_rows(raw, *, minimum_tick=4):
    """No new radio/actor query; eligibility uses the saved *causal* boundary."""
    if int(raw['completed_steps']) != 256 or str(raw['program']) != 'M':
        raise ValueError('only complete actual M-suffix episodes can supply targets')
    records = unpack_records(raw)
    sites = p.decode_map(raw['map_packet'].tobytes())
    last, maximum, windows = contact_states(raw['model_contacts'])
    _, actual_maximum, _ = contact_states(raw['connections'].any(axis=1))
    xs, ys, ticks, missing = [], [], [], []
    for index, record in enumerate(records):
        tick = index * 4
        if tick < minimum_tick or tick == 0:
            continue
        if not (record['decoded_anchor'] and record['history_start'] == 0
                and record['history_after'] == tick and raw['model_valid'][:tick].all()):
            missing.append(tick)
            continue
        positions, actual, _, _ = p.decode_reports(
            tuple(packet.tobytes() for packet in record['report_packets']), tick)
        # Past contacts in the terminal container are accepted only after they match
        # the history that this actor actually had at the boundary.
        np.testing.assert_array_equal(last[tick], record['history_last'])
        np.testing.assert_array_equal(windows[tick], record['history_windows'])
        if 'history_maximum' in record:
            np.testing.assert_array_equal(maximum[tick], record['history_maximum'])
        xs.append(pack_features(sites=sites, positions=positions, commands=actual,
            mask=int(raw['mask'][tick]), previous_nav=raw['post_c_nav'][index - 1],
            last=last[tick], maximum=maximum[tick], windows=windows[tick],
            tick=tick, history_start=0, history_after=tick))
        ys.append(float((actual_maximum[-1] - actual_maximum[tick]).mean()))
        ticks.append(tick)
    return dict(X=np.asarray(xs, np.float32).reshape(-1, FEATURE_DIM), y=np.array(ys, np.float64),
                ticks=np.array(ticks, np.int64), missing_ticks=missing)


def build_dataset(sources):
    xs, ys, ids, ticks, rows = [], [], [], [], []
    for episode, source in enumerate(sources):
        identity = source['raw']
        if file_identity(Path(identity['path'])) != identity:
            raise ValueError('acquisition raw identity changed')
        raw = load_episode(Path(identity['path']))
        if int(raw['world_seed']) != source['seed']:
            raise ValueError('source world identity mismatch')
        perturb = int(source.get('perturbation_tick', -1))
        if 'perturbation_tick' in raw and int(raw['perturbation_tick']) != perturb:
            raise ValueError('perturbation identity mismatch')
        data = episode_rows(raw, minimum_tick=max(4, perturb + 4))
        xs.append(data['X']); ys.append(data['y'])
        ids.append(np.full(len(data['y']), episode, np.int64)); ticks.append(data['ticks'])
        rows.append(dict(episode=episode, seed=source['seed'], source=identity,
                         perturbation_tick=perturb, labels=len(data['y']),
                         missing_ticks=data['missing_ticks']))
    if not xs or not sum(map(len, ys)):
        raise ValueError('no lawful training rows')
    return dict(X=np.concatenate(xs), y=np.concatenate(ys), episode_ids=np.concatenate(ids),
                ticks=np.concatenate(ticks)), rows
