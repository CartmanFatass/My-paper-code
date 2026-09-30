"""Failure-only bounded operand evidence; never installed on the normal path."""

import json
import math
from pathlib import Path

import numpy as np


MAX_ARRAY_ELEMENTS = 5000
MAX_TOTAL_ELEMENTS = 50000
MAX_ARRAYS = 64
MAX_FRAMES = 24
MAX_TRACEBACK_FRAMES = 256
MAX_CHAIN = 8
MAX_SEQUENCE_ITEMS = 64
MAX_TEXT = 2048

RADIO = 'envs/pettingzoo/uav_radio.py'
SCHEDULER = 'experiments/candidates/uav_user_waiting/b02/scheduler.py'
DIRECT_SUPPORT = (
    'experiments/candidates/uav_local_history/b01/controller.py',
    'experiments/candidates/uav_registered_service/b01/history.py',
    'experiments/candidates/uav_user_waiting/b01/history.py',
)
OPERANDS = (
    'sinr', 'values', 'flat', 'eligible', 'order', 'position', 'n_uavs', 'n_users',
    'uav_idx', 'user_idx', 'connections', 'uav_connections', 'user_connected',
    'connected_total', 'full_uavs', 'min_sinr', 'max_connections', 'transmitter_mask',
    'mask', 'current_mask', 'q', 'slot', 'losses', 'positions', 'actual', 'proposals',
    'actual_wire', 'proposed_wire', 'nav_wire', 'nav_indices', 'tick', 'at_tick',
    'member', 'selected', 'pair', 'first_q', 'first_mask', 'motion', 'mask_pair',
    'own', 'served', 'contacts', 'commands', 'origin', 'stop', 'decoded_position',
    'xy', 'peers', 'points', 'current', 'observed_indices', 'sinr_observed',
    'endpoints', 'index', 'age', 'native',
)


def _type(value):
    cls = type(value)
    return cls.__module__ + '.' + cls.__qualname__


def _text(value):
    try:
        message = str(value)
        return message[:MAX_TEXT], len(message) > MAX_TEXT, True
    except BaseException:
        return '<message unavailable>', False, False


def _scalar(value):
    if type(value) in (bool, int, str) or value is None:
        return value[:MAX_TEXT] if type(value) is str else value
    if type(value) is float:
        return value if math.isfinite(value) else ('nan' if math.isnan(value) else ('inf' if value > 0 else '-inf'))
    raise TypeError('not a supported scalar')


def capture_failure(exc, out):
    """Best-effort create-only capture, returning errors instead of raising them.

    It deliberately neither clears traceback frames nor executes arbitrary object
    representations. Array values are numeric only, with bounded C-order prefixes
    for large operands. Caller retains and rethrows its original exception.
    """
    errors, arrays = [], {}
    result = dict(kind='bounded-traceback-operands', json_written=False, npz_written=False,
                  selected_frames=0, arrays=0, captured_elements=0, capture_errors=errors)
    record = dict(kind=result['kind'], limits=dict(array_elements=MAX_ARRAY_ELEMENTS,
                  total_elements=MAX_TOTAL_ELEMENTS, arrays=MAX_ARRAYS, frames=MAX_FRAMES,
                  traceback_frames=MAX_TRACEBACK_FRAMES, exception_chain=MAX_CHAIN,
                  sequence_items=MAX_SEQUENCE_ITEMS), exceptions=[], frames=[], capture_errors=errors,
                  chain_truncated=False, traceback_truncated=False, selected_frames_truncated=False)

    def error(where, failure):
        errors.append(dict(where=where, type=_type(failure)))

    def operand(value, key):
        meta = dict(type=_type(value))
        if type(value) is np.ndarray or isinstance(value, np.generic):
            array = np.asarray(value)
            meta.update(dtype=str(array.dtype), shape=list(array.shape), size=int(array.size))
            if array.dtype.kind not in 'biufc' or array.dtype.hasobject or array.dtype.itemsize > 32:
                meta['omitted'] = 'non-numeric/object/oversize dtype'
                return meta
            allowance = min(MAX_ARRAY_ELEMENTS, MAX_TOTAL_ELEMENTS - result['captured_elements'])
            if len(arrays) >= MAX_ARRAYS or (array.size and allowance <= 0):
                meta.update(omitted='global array budget', truncated=True)
                return meta
            count = min(int(array.size), allowance)
            captured = array.copy(order='C') if count == array.size else array.flat[:count].copy()
            arrays[key] = captured
            result['captured_elements'] += count
            meta.update(array_key=key, captured_shape=list(captured.shape), captured_elements=count,
                        truncated=count < array.size, layout='original shape' if count == array.size else 'C-flat prefix')
            return meta
        if type(value) in (bool, int, float, str) or value is None:
            meta['value'] = _scalar(value)
            meta['truncated'] = type(value) is str and len(value) > MAX_TEXT
            return meta
        if type(value) in (list, tuple):
            meta.update(length=len(value), truncated=len(value) > MAX_SEQUENCE_ITEMS)
            items = []
            for item in value[:MAX_SEQUENCE_ITEMS]:
                if type(item) in (bool, int, float, str) or item is None:
                    items.append(dict(type=_type(item), value=_scalar(item)))
                elif isinstance(item, np.generic) and item.dtype.kind in 'biuf':
                    items.append(dict(type=_type(item), dtype=str(item.dtype), value=_scalar(item.item())))
                else:
                    items.append(dict(type=_type(item), omitted='not a plain scalar'))
            meta['items'] = items
            return meta
        meta['omitted'] = 'object values are not serialized'
        return meta

    def operands(values, key_prefix):
        captured = {}
        for name in OPERANDS:
            if name in values:
                try:
                    captured[name] = operand(values[name], key_prefix + '_' + name)
                except BaseException as failure:
                    error(key_prefix + '.' + name, failure)
        return captured

    def known_state(value, key_prefix):
        """Only fixed fields of source-owned state; never generic recursion."""
        cls = type(value)
        if cls.__module__ not in (
            'experiments.candidates.uav_user_waiting.b02.scheduler',
            'experiments.candidates.uav_user_waiting.b01.history',
            'experiments.candidates.uav_registered_service.b01.history',
            'experiments.candidates.uav_local_history.b01.controller',
        ):
            return dict(type=_type(value), omitted='state type outside selected sources')
        state = object.__getattribute__(value, '__dict__')
        fields = ('tick', 'mask', 'member', 'proposal_q', 'length', 'positions', 'actual', 'proposals',
                  'sites', 'arm', 'horizon', 'start_tick', 'last', 'windows', 'burden',
                  'next_unsettled', 'position', '_nav_index', '_points', '_command')
        captured = dict(type=_type(value), fields={})
        for name in fields:
            if name in state:
                try:
                    captured['fields'][name] = operand(state[name], key_prefix + '_' + name)
                except BaseException as failure:
                    error(key_prefix + '.' + name, failure)
        return captured

    try:
        seen, current, relation = set(), exc, 'raised'
        traversed = 0
        for chain_index in range(MAX_CHAIN):
            if current is None or id(current) in seen:
                record['chain_truncated'] = current is not None
                break
            seen.add(id(current))
            message, truncated, available = _text(current)
            entry = dict(type=_type(current), message=message, message_truncated=truncated,
                         message_available=available, relation=relation)
            record['exceptions'].append(entry)
            if not available:
                errors.append(dict(where='exception_message', type='representation_unavailable'))
            traceback = current.__traceback__
            while traceback is not None:
                if traversed >= MAX_TRACEBACK_FRAMES:
                    record['traceback_truncated'] = True
                    break
                traversed += 1
                frame, code = traceback.tb_frame, traceback.tb_frame.f_code
                path = code.co_filename.replace('\\', '/')
                radio = path.endswith('/' + RADIO) or path == RADIO
                scheduler = (path.endswith('/' + SCHEDULER) or path == SCHEDULER) and code.co_name in ('score', 'prepare', 'decide', 'search', 'choose')
                direct = traceback.tb_next is None and any(path.endswith('/' + target) or path == target for target in DIRECT_SUPPORT)
                if radio or scheduler or direct:
                    if len(record['frames']) >= MAX_FRAMES:
                        record['selected_frames_truncated'] = True
                    else:
                        number = len(record['frames'])
                        key_prefix = 'frame_' + str(number)
                        values = frame.f_locals
                        captured = dict(exception_index=chain_index, path=code.co_filename,
                                        function=code.co_name, line=traceback.tb_lineno,
                                        operands=operands(values, key_prefix), state={})
                        for name in ('self', 'private', 'prefix', 'history', 'settled'):
                            if name in values:
                                try:
                                    captured['state'][name] = known_state(values[name], key_prefix + '_' + name)
                                except BaseException as failure:
                                    error(key_prefix + '.' + name, failure)
                        record['frames'].append(captured)
                traceback = traceback.tb_next
            cause, context = current.__cause__, current.__context__
            current, relation = (cause, 'cause') if cause is not None else (context, 'context')
            if current is None:
                break
        else:
            record['chain_truncated'] = current is not None
        folder = Path(out)
        json_path, npz_path = folder / 'failure-operands.json', folder / 'failure-operands.npz'
        result.update(json_path=str(json_path), npz_path=str(npz_path))
        # Both are create-only. Refuse an existing member rather than producing
        # a new sidecar which might be mistaken for its original counterpart.
        if json_path.exists() or npz_path.exists():
            raise FileExistsError('failure capture already exists')
        try:
            with npz_path.open('xb') as stream:
                np.savez_compressed(stream, **arrays)
            result['npz_written'] = True
        except BaseException as failure:
            error('write_npz', failure)
        record['npz_written'] = result['npz_written']
        try:
            with json_path.open('x', encoding='utf-8') as stream:
                json.dump(record, stream, ensure_ascii=False, allow_nan=False, indent=2)
            result['json_written'] = True
        except BaseException as failure:
            error('write_json', failure)
    except BaseException as failure:
        error('capture', failure)
    result.update(selected_frames=len(record['frames']), arrays=len(arrays))
    return result
