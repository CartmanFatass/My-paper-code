"""Frozen, unnormalised causal feature layout. Missing values are zero-filled.

Every availability field is itself a feature. No actual service/age enters here.
The coordinate and age scales are fixed to the H256/U50 host, including short
correctness horizons; there is no fitted normaliser or clipping of model ages.
"""

import numpy as np

from experiments.candidates.uav_radio_activation.b03.protocol import HIGH, LOW


_FIELDS = (
    ('map', 100, 'metres / 1000'),
    ('positions', 15, '(metres - LOW) / (HIGH - LOW); missing = 0'),
    ('actual_commands', 15, 'command units'),
    ('actual_mask', 5, 'transmitter bits'),
    ('proposals', 15, 'command units; decoded report only'),
    ('pending_commands', 15, 'command units; always 0 at report'),
    ('pending_mask', 5, 'bits; always 0 at report'),
    ('pending_available', 1, 'always 0 at report'),
    ('model_ages', 50, 'age at last settled tick / 256'),
    ('model_unknown', 50, 'censored unseen indicator'),
    ('prefix_ages', 50, 'age at end of delivery prefix / 256'),
    ('prefix_unknown', 50, 'censored unseen indicator'),
    ('clock', 5, 'tick/256, remaining/256, scored_length/4, model_tick/256, unsettled/256'),
    ('mover', 5, 'one hot rotating member'),
    ('availability', 4, 'decoded position, decoded proposal, model history, complete prefix'),
    ('O_commands', 15, 'command units; missing = 0'),
    ('O_mask', 5, 'transmitter bits; missing = 0'),
    ('O_endpoint_ages', 50, 'age at end of candidate / 256; missing = 0'),
    ('O_endpoint_unknown', 50, 'censored unseen indicator; missing = 0'),
    ('O_summary', 4, 'J, served/50, quality, cumulative age/(50*256*4); missing = 0'),
    ('O_available', 1, 'complete O plan indicator'),
    ('W_commands', 15, 'command units; missing = 0'),
    ('W_mask', 5, 'transmitter bits; missing = 0'),
    ('W_endpoint_ages', 50, 'age at end of candidate / 256; missing = 0'),
    ('W_endpoint_unknown', 50, 'censored unseen indicator; missing = 0'),
    ('W_summary', 4, 'J, served/50, quality, cumulative age/(50*256*4); missing = 0'),
    ('W_available', 1, 'complete W plan indicator'),
)


def _specification():
    offset, fields = 0, []
    for name, size, scale in _FIELDS:
        fields.append(dict(name=name, start=offset, stop=offset + size, scale=scale))
        offset += size
    return dict(version=1, dtype='float32', dim=offset, fixed_horizon=256,
                fixed_users=50, missing_fill=0, fields=fields)


FEATURE_SPEC = _specification()
FEATURE_DIM = FEATURE_SPEC['dim']
FEATURE_SLICES = {f['name']: slice(f['start'], f['stop']) for f in FEATURE_SPEC['fields']}


def model_ages(last, end_tick):
    """Post-transition age: last=-1 gives end_tick+1, including origin tick0."""
    return int(end_tick) - np.asarray(last, dtype=np.int64)


def mask_bits(mask):
    return ((int(mask) >> np.arange(5)) & 1).astype(np.float32)


def pack_features(record, sites, actual_commands, current_mask, *, tick, horizon):
    """Pack only the report's saved causal data, never the eventual settled log."""
    features = np.zeros(FEATURE_DIM, dtype=np.float32)

    def put(name, value):
        features[FEATURE_SLICES[name]] = np.asarray(value, dtype=np.float32).reshape(-1)

    put('map', np.asarray(sites) / 1000.)
    put('actual_commands', actual_commands)
    put('actual_mask', mask_bits(current_mask))
    if record['decoded_anchor']:
        put('positions', (record['decoded_positions'] - LOW) / (HIGH - LOW))
        put('proposals', record['decoded_proposals'])
    history_available = record['history_start'] >= 0
    if history_available:
        put('model_ages', model_ages(record['model_last'], record['model_tick']) / 256.)
        put('model_unknown', record['unknown_age'])
    if record['prefix_valid']:
        put('prefix_ages', model_ages(record['prefix_last'], tick + 1) / 256.)
        put('prefix_unknown', record['prefix_unknown'])
    put('clock', [tick / 256., (horizon - tick) / 256., record['scored_length'] / 4.,
                  record['model_tick'] / 256. if history_available else 0.,
                  (tick - record['history_after']) / 256.])
    mover = np.zeros(5)
    mover[(tick // 4) % 5] = 1
    put('mover', mover)
    put('availability', [record['decoded_anchor'], record['decoded_anchor'],
                         history_available, record['prefix_valid']])
    for index, label in enumerate(('O', 'W')):
        if not record['plan_available'][index]:
            continue
        put(label + '_commands', record['plan_commands'][index])
        put(label + '_mask', mask_bits(record['plan_masks'][index]))
        put(label + '_endpoint_ages', record['plan_endpoint_ages'][index] / 256.)
        put(label + '_endpoint_unknown', record['plan_endpoint_unknown'][index])
        native = record['plan_scores'][index]
        put(label + '_summary', [native[0], native[1] / 50., native[2],
                                 record['plan_costs'][index] / 51200.])
        put(label + '_available', 1)
    if not np.isfinite(features).all():
        raise ValueError('nonfinite causal features')
    return features
