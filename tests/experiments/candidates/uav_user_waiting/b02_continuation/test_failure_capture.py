"""Synthetic traceback capture fixtures; no radio call or native environment."""

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02_continuation import failure_capture as capture


def synthetic_failure(*, large=False, extra=''):
    namespace = {'np': np, 'large': large, '__name__': 'synthetic.radio'}
    radio_source = '''
def greedy_connection_assignment(sinr):
    values = sinr
    flat = values.reshape(-1)
    eligible = np.arange(flat.size, dtype=np.int64)
    order = eligible[::-1].copy()
    n_uavs, n_users = values.shape
    position = np.array([0, 1], dtype=np.int64)
    uav_idx = position // n_users
    user_idx = position - uav_idx * n_users
    user_connected = [False] * n_users
    uav_connections = [0] * n_uavs
EXTRA
    return user_connected[user_idx]
'''.replace('EXTRA', extra)
    exec(compile(radio_source, '/accepted/envs/pettingzoo/uav_radio.py', 'exec'), namespace)
    scheduler_source = '''
def score(q, mask):
    slot = 2
    positions = np.arange(15, dtype=np.float64).reshape(5, 3)
    losses = np.ones((5, 50), dtype=np.float64)
    sinr = np.arange(20000 if large else 250, dtype=np.float64).reshape(100, 200) if large else np.arange(250, dtype=np.float64).reshape(5, 50)
    return greedy_connection_assignment(sinr)
def decide():
    tick = 112
    current_mask = 31
    actual_wire = np.zeros((5, 3))
    return score(10, 15)
'''
    exec(compile(scheduler_source, '/accepted/experiments/candidates/uav_user_waiting/b02/scheduler.py', 'exec'), namespace)
    try:
        namespace['decide']()
    except TypeError as exc:
        return exc
    raise AssertionError('fixture did not raise')


def load_json(out):
    return json.loads((out / 'failure-operands.json').read_text())


def frame(record, name):
    return next(entry for entry in record['frames'] if entry['function'] == name)


def test_assignment_corruption_operands_and_scalar_metadata_are_exact(tmp_path):
    exc = synthetic_failure()
    original_traceback = exc.__traceback__
    result = capture.capture_failure(exc, tmp_path)
    assert result['json_written'] and result['npz_written'] and not result['capture_errors']
    assert exc.__traceback__ is original_traceback
    record = load_json(tmp_path)
    assert record['exceptions'][0]['type'] == 'builtins.TypeError'
    assert 'integer scalar' in record['exceptions'][0]['message']
    assignment = frame(record, 'greedy_connection_assignment')
    operands = assignment['operands']
    assert operands['n_uavs']['value'] == 5 and operands['n_users']['value'] == 50
    assert operands['user_connected']['items'][0]['value'] is False
    assert assignment['path'].endswith(capture.RADIO) and assignment['line'] > 0
    score = frame(record, 'score')['operands']
    assert score['q']['value'] == 10 and score['mask']['value'] == 15 and score['slot']['value'] == 2
    with np.load(tmp_path / 'failure-operands.npz', allow_pickle=False) as arrays:
        expected = np.arange(250, dtype=np.float64).reshape(5, 50)
        for name, value in [('sinr', expected), ('values', expected), ('flat', expected.reshape(-1)),
                            ('eligible', np.arange(250)), ('order', np.arange(249, -1, -1)),
                            ('position', [0, 1]), ('uav_idx', [0, 0]), ('user_idx', [0, 1])]:
            meta = operands[name]
            np.testing.assert_array_equal(arrays[meta['array_key']], value)
            assert not meta['truncated']
            assert meta['dtype'] == str(arrays[meta['array_key']].dtype)
        np.testing.assert_array_equal(arrays[score['positions']['array_key']], np.arange(15).reshape(5, 3))


def test_large_arrays_store_only_declared_c_prefix_and_budget(tmp_path):
    result = capture.capture_failure(synthetic_failure(large=True), tmp_path)
    record = load_json(tmp_path)
    meta = frame(record, 'greedy_connection_assignment')['operands']['values']
    assert meta['shape'] == [100, 200] and meta['size'] == 20000
    assert meta['captured_shape'] == [5000] and meta['truncated']
    assert meta['layout'] == 'C-flat prefix'
    with np.load(tmp_path / 'failure-operands.npz', allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays[meta['array_key']], np.arange(5000))
        assert all(value.size <= capture.MAX_ARRAY_ELEMENTS for value in arrays.values())
        assert sum(value.size for value in arrays.values()) == result['captured_elements']
        assert result['captured_elements'] <= capture.MAX_TOTAL_ELEMENTS


def test_many_traceback_frames_and_arrays_stop_at_global_limits(tmp_path):
    namespace = {'np': np}
    source = '''
def score(depth):
    sinr = np.arange(6000, dtype=np.int64)
    if depth:
        return score(depth - 1)
    raise RuntimeError('bounded recursive synthetic failure')
'''
    exec(compile(source, capture.SCHEDULER, 'exec'), namespace)
    try:
        namespace['score'](40)
    except RuntimeError as exc:
        result = capture.capture_failure(exc, tmp_path)
    record = load_json(tmp_path)
    assert result['selected_frames'] == capture.MAX_FRAMES
    assert record['selected_frames_truncated']
    assert result['captured_elements'] == capture.MAX_TOTAL_ELEMENTS
    assert any(entry['operands']['sinr'].get('omitted') == 'global array budget' for entry in record['frames'])
    with np.load(tmp_path / 'failure-operands.npz', allow_pickle=False) as arrays:
        assert len(arrays.files) <= capture.MAX_ARRAYS


def test_exception_chain_and_direct_history_frame_are_preserved(tmp_path):
    namespace = {'np': np}
    source = '''
def update():
    tick = 255
    served = np.ones(50, bool)
    raise ValueError('synthetic history failure')
'''
    exec(compile(source, capture.DIRECT_SUPPORT[-1], 'exec'), namespace)
    try:
        try:
            namespace['update']()
        except ValueError as original:
            raise RuntimeError('outer collection wrapper') from original
    except RuntimeError as exc:
        result = capture.capture_failure(exc, tmp_path)
    assert result['json_written']
    record = load_json(tmp_path)
    assert [entry['relation'] for entry in record['exceptions']] == ['raised', 'cause']
    assert [entry['type'] for entry in record['exceptions']] == ['builtins.RuntimeError', 'builtins.ValueError']
    assert frame(record, 'update')['operands']['tick']['value'] == 255


def test_trusted_stage_state_fields_are_shallow_and_faithful(tmp_path):
    namespace = {'np': np, '__name__': 'experiments.candidates.uav_user_waiting.b02.scheduler'}
    source = '''
class _Stage:
    def __init__(self):
        self.tick = 112
        self.mask = 15
        self.positions = np.arange(15, dtype=np.float64).reshape(5, 3)
        self.record = {'deep': object()}
    def score(self, q, mask):
        raise RuntimeError('synthetic stage')
'''
    exec(compile(source, capture.SCHEDULER, 'exec'), namespace)
    try:
        namespace['_Stage']().score(10, 15)
    except RuntimeError as exc:
        capture.capture_failure(exc, tmp_path)
    state = frame(load_json(tmp_path), 'score')['state']['self']
    assert state['fields']['tick']['value'] == 112 and state['fields']['mask']['value'] == 15
    assert 'record' not in state['fields']
    with np.load(tmp_path / 'failure-operands.npz', allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays[state['fields']['positions']['array_key']], np.arange(15).reshape(5, 3))


def test_hostile_representations_object_arrays_and_nonfinite_scalars_are_safe(tmp_path):
    class Hostile:
        def __repr__(self):
            pytest.fail('object representation must never be evaluated')

    class HostileException(Exception):
        def __str__(self):
            raise RuntimeError('hostile exception string')

    namespace = {'np': np, 'Hostile': Hostile, 'HostileException': HostileException}
    source = '''
def score():
    values = np.array([Hostile()], dtype=object)
    position = Hostile()
    min_sinr = float('nan')
    max_connections = float('inf')
    eligible = [Hostile()]
    raise HostileException()
'''
    exec(compile(source, capture.SCHEDULER, 'exec'), namespace)
    try:
        namespace['score']()
    except HostileException as exc:
        result = capture.capture_failure(exc, tmp_path)
    assert result['json_written'] and result['npz_written']
    assert result['capture_errors'][0]['where'] == 'exception_message'
    record = load_json(tmp_path)
    operands = frame(record, 'score')['operands']
    assert operands['values']['dtype'] == 'object' and 'array_key' not in operands['values']
    assert operands['position']['omitted'] == 'object values are not serialized'
    assert operands['min_sinr']['value'] == 'nan' and operands['max_connections']['value'] == 'inf'


def test_io_errors_do_not_replace_original_exception(tmp_path, monkeypatch):
    original = synthetic_failure()
    old_open = Path.open

    def fail_open(path, *args, **kwargs):
        if path.name.startswith('failure-operands.'):
            raise OSError('synthetic unavailable output')
        return old_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', fail_open)
    with pytest.raises(TypeError) as caught:
        try:
            raise original
        except TypeError as exc:
            result = capture.capture_failure(exc, tmp_path)
            raise
    assert caught.value is original
    assert not result['json_written'] and not result['npz_written']
    assert {item['where'] for item in result['capture_errors']} == {'write_npz', 'write_json'}
    json.dumps(result, allow_nan=False)


def test_sidecars_are_create_only(tmp_path):
    first = capture.capture_failure(synthetic_failure(), tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    second = capture.capture_failure(synthetic_failure(large=True), tmp_path)
    assert first['json_written'] and not second['json_written'] and not second['npz_written']
    assert second['capture_errors'][-1]['type'] == 'builtins.FileExistsError'
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
