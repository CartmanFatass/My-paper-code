"""Lossless, pickle-free storage of variable-size decision records in one NPZ."""

import json

import numpy as np


def pack_records(records):
    chunks, offset = [], 0

    def encode(value):
        nonlocal offset
        if isinstance(value, np.ndarray):
            array = np.ascontiguousarray(value)
            if array.dtype.hasobject:
                raise TypeError('object arrays cannot be scientific evidence')
            data = array.tobytes()
            entry = {'array': [array.dtype.str, list(value.shape), offset, len(data)]}
            chunks.append(data)
            offset += len(data)
            return entry
        if isinstance(value, np.generic):
            return encode(value.item())
        if isinstance(value, float) and not np.isfinite(value):
            return {'nonfinite': 'nan' if np.isnan(value) else ('inf' if value > 0 else '-inf')}
        if isinstance(value, dict):
            return {'dict': [[str(key), encode(item)] for key, item in value.items()]}
        if isinstance(value, (list, tuple)):
            return {'list': [encode(item) for item in value]}
        if value is None or isinstance(value, (str, bool, int, float)):
            return {'scalar': value}
        raise TypeError(f'unsupported evidence value: {type(value).__name__}')

    schema = json.dumps(encode(records), separators=(',', ':'), allow_nan=False)
    return dict(decision_schema=np.array(schema),
                decision_bytes=np.frombuffer(b''.join(chunks), dtype=np.uint8))


def unpack_records(raw):
    schema = json.loads(str(raw['decision_schema']))
    data = np.asarray(raw['decision_bytes'], dtype=np.uint8)
    consumed = 0

    def decode(entry):
        nonlocal consumed
        if len(entry) != 1:
            raise ValueError('invalid decision schema')
        if 'array' in entry:
            dtype, shape, offset, size = entry['array']
            dtype = np.dtype(dtype)
            if dtype.hasobject or any(not isinstance(n, int) or n < 0 for n in shape):
                raise ValueError('unsafe decision array')
            if offset != consumed or size != int(np.prod(shape, dtype=np.int64)) * dtype.itemsize:
                raise ValueError('non-contiguous or inconsistent decision array')
            if offset + size > data.nbytes:
                raise ValueError('truncated decision bytes')
            consumed += size
            return np.frombuffer(data[offset:offset + size], dtype=dtype).reshape(shape).copy()
        if 'dict' in entry:
            pairs = entry['dict']
            if len({key for key, _ in pairs}) != len(pairs):
                raise ValueError('duplicate evidence key')
            return {key: decode(value) for key, value in pairs}
        if 'list' in entry:
            return [decode(value) for value in entry['list']]
        if 'scalar' in entry:
            return entry['scalar']
        if 'nonfinite' in entry and entry['nonfinite'] in ('nan', 'inf', '-inf'):
            return float(entry['nonfinite'])
        raise ValueError('unknown decision schema item')

    records = decode(schema)
    if consumed != data.nbytes:
        raise ValueError('unbound decision bytes')
    return records
