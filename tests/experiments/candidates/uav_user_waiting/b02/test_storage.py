"""Evidence serialization must preserve types and reject unbound payloads."""

import json

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records


def test_numeric_record_roundtrip_without_pickle(tmp_path):
    records = [{'tick': 248, 'partial': {}, 'pairs': np.array([[1, 2], [3, 31]], dtype=np.int64),
                'contacts': np.array([[True, False]], dtype=bool),
                'missing': np.full((0, 3), np.nan), 'labels': np.array(['S', 'W']),
                'scalar': np.array(7, dtype=np.int16), 'tuples': (True, None, 'x'),
                'not_observed': float('nan'), 'infinity': float('inf')}]
    packed = pack_records(records)
    path = tmp_path / 'evidence.npz'
    np.savez_compressed(path, **packed)
    with np.load(path, allow_pickle=False) as raw:
        restored = unpack_records(raw)[0]
    for key in ('pairs', 'contacts', 'missing', 'labels', 'scalar'):
        np.testing.assert_array_equal(restored[key], records[0][key])
        assert restored[key].dtype == records[0][key].dtype
        assert restored[key].shape == records[0][key].shape
    assert restored['tuples'] == [True, None, 'x']
    assert np.isnan(restored['not_observed']) and restored['infinity'] == float('inf')


def test_rejects_object_payload():
    with pytest.raises(TypeError, match='object arrays'):
        pack_records([np.array([object()], dtype=object)])


@pytest.mark.parametrize('change', ['truncated', 'extra', 'offset'])
def test_rejects_corrupt_evidence_buffer(change):
    packed = pack_records(np.arange(4, dtype=np.int64))
    if change == 'truncated':
        packed['decision_bytes'] = packed['decision_bytes'][:-1]
    elif change == 'extra':
        packed['decision_bytes'] = np.append(packed['decision_bytes'], np.uint8(0))
    else:
        schema = json.loads(str(packed['decision_schema']))
        schema['array'][2] = 1
        packed['decision_schema'] = np.array(json.dumps(schema))
    with pytest.raises(ValueError):
        unpack_records(packed)
