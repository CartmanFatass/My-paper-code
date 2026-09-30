"""Fixed 805 legal boundary features; no fitted scaler or radio queries."""

import numpy as np


FEATURE_DIM = 805
HORIZON = 256
LOW = np.array([0., 0., 50.])
HIGH = np.array([1000., 1000., 150.])
DISTANCE_SCALE = float(np.sqrt(1000.**2 + 1000.**2 + 150.**2))
_FIELDS = (
    ('sites', 100), ('positions', 15), ('commands', 15), ('mask', 5),
    ('previous_nav', 50), ('age', 50), ('maximum', 50), ('windows', 200),
    ('unserved', 50), ('availability', 3), ('clock', 2), ('member', 5),
    ('relations', 250), ('pooled', 10),
)
FEATURE_SLICES = {}
_offset = 0
for _name, _size in _FIELDS:
    FEATURE_SLICES[_name] = slice(_offset, _offset + _size)
    _offset += _size
assert _offset == FEATURE_DIM
FEATURE_SPEC = dict(
    version=1, dim=FEATURE_DIM, dtype='float32', horizon=HORIZON,
    fields=[dict(name=name, start=FEATURE_SLICES[name].start,
                 stop=FEATURE_SLICES[name].stop) for name, _ in _FIELDS],
    relations=['d', 'd_squared', 'slack', 'd_age', 'd_slack'],
    relation_layout='user-major',
    pooled=['age_mean', 'age_second_moment', 'maximum_mean', 'maximum_second_moment',
            'slack_mean', 'slack_second_moment', 'd_mean', 'd_second_moment',
            'd_age_mean', 'd_slack_mean'],
)


def _integer(value):
    return isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))


def pack_features(*, sites, positions, commands, mask, previous_nav, last,
                  maximum, windows, tick, history_start, history_after):
    """Pack only complete origin-to-boundary history and decoded model geometry.

    Age at boundary t is t-1-last, with a-minus(0)=0. The previous navigation
    bytes precede the next C call; current/future proposals are not inputs.
    """
    if not _integer(tick) or tick not in range(0, HORIZON + 1, 4):
        raise ValueError('value boundary must be a four-tick boundary in0..256')
    if not _integer(history_start) or not _integer(history_after) or history_start != 0 or history_after != tick:
        raise ValueError('complete causal origin-to-boundary history required')
    sites = np.asarray(sites, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.float64)
    commands = np.asarray(commands)
    previous_nav, last, maximum, windows = map(np.asarray, (previous_nav, last, maximum, windows))
    if sites.shape not in ((50, 2), (50, 3)) or not np.isfinite(sites).all():
        raise ValueError('decoded map must have50finite XY rows')
    sites = sites[:, :2]
    if np.any((sites < 0.) | (sites > 1000.)):
        raise ValueError('decoded map outside native bounds')
    if positions.shape != (5, 3) or not np.isfinite(positions).all() or np.any(positions < LOW) or np.any(positions > HIGH):
        raise ValueError('decoded anchors must have5bounded finite XYZ rows')
    if not np.array_equal(positions, np.rint(positions)):
        raise ValueError('anchors must already be decoded on the integer grid')
    if commands.shape != (5, 3) or not np.isin(commands, (-1, 0, 1)).all():
        raise ValueError('invalid effective commands')
    if not _integer(mask) or not 1 <= mask <= 31:
        raise ValueError('effective mask must be nonempty')
    for name, value, shape in (('previous_nav', previous_nav, (5,)), ('last', last, (50,)), ('maximum', maximum, (50,))):
        if value.shape != shape or value.dtype.kind not in 'iu':
            raise ValueError(name + ' must be an integer array of the declared shape')
    if np.any((previous_nav < 0) | (previous_nav > 9)):
        raise ValueError('previous navigation byte outside0..9')
    if windows.shape != (4, 50) or windows.dtype != np.dtype(bool):
        raise ValueError('window contacts must be four-by50 booleans')
    if np.any(last < -1) or np.any(last >= tick) or np.any(maximum < 0) or np.any(maximum > tick):
        raise ValueError('last-service/maximum history is outside the completed prefix')
    if tick == 0:
        age = np.zeros(50, dtype=np.int64)
    else:
        age = np.int64(tick - 1) - last.astype(np.int64)
    if np.any(maximum < age) or (tick == 0 and (maximum.any() or windows.any())):
        raise ValueError('modeled maxima cannot be smaller than current age')
    possible_maximum = np.where(last < 0, tick, np.maximum(last, age))
    if np.any(maximum > possible_maximum):
        raise ValueError('modeled maxima cannot exceed the possible completed history')
    if np.any(windows[np.arange(4) * 64 >= tick]):
        raise ValueError('future window contacts are unavailable')
    latest_window = np.where(windows, np.arange(4)[:, None], -1).max(axis=0)
    expected_window = np.where(last < 0, -1, last // 64)
    if not np.array_equal(latest_window, expected_window):
        raise ValueError('last-service and window contacts disagree')
    active = ((int(mask) >> np.arange(5)) & 1).astype(bool)
    delta = positions[active, None, :] - np.column_stack((sites, np.zeros(50)))[None, :, :]
    distance = np.sqrt(np.square(delta).sum(axis=2)).min(axis=0) / DISTANCE_SCALE
    age_scaled, maximum_scaled = age / HORIZON, maximum.astype(np.float64) / HORIZON
    slack = maximum_scaled - age_scaled
    relations = np.column_stack((distance, distance**2, slack, distance * age_scaled, distance * slack))
    pooled = np.array([age_scaled.mean(), np.square(age_scaled).mean(),
                       maximum_scaled.mean(), np.square(maximum_scaled).mean(),
                       slack.mean(), np.square(slack).mean(), distance.mean(), np.square(distance).mean(),
                       (distance * age_scaled).mean(), (distance * slack).mean()])
    member = np.zeros(5)
    member[(int(tick) // 4) % 5] = 1.
    blocks = dict(sites=sites / 1000., positions=(positions - LOW) / (HIGH - LOW), commands=commands,
                  mask=active, previous_nav=np.eye(10)[previous_nav.astype(int)], age=age_scaled,
                  maximum=maximum_scaled, windows=windows, unserved=last < 0,
                  availability=np.ones(3), clock=[tick / HORIZON, (HORIZON - tick) / HORIZON],
                  member=member, relations=relations, pooled=pooled)
    result = np.empty(FEATURE_DIM, dtype=np.float32)
    for name, block in blocks.items():
        result[FEATURE_SLICES[name]] = np.asarray(block, dtype=np.float32).reshape(-1)
    if not np.isfinite(result).all():
        raise ValueError('nonfinite legal features')
    return result
