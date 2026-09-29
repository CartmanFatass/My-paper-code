"""Version-two public reports and delayed motion/activation commitments."""

import struct

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.protocol import (
    ALL_ON, HIGH, HOLD, HORIZON, LOW, N, U, decode_map, encode_map, mask_array,
)


SEED = 29306000
WORLDS = 64
DEADLINE_SECONDS = 4.0 - (N * 24 + 16) * 8 / 2000.0
REPORT = struct.Struct('<BBBBIIhhhbbbbbb')
COMMAND = struct.Struct('<BBBBIII')
REPORT_TICKS = range(0, HORIZON - HOLD, HOLD)


def command_index(command):
    value = np.asarray(command)
    if value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError('command must be a finite three-vector')
    matches = np.flatnonzero(np.all(COMMANDS == value, axis=1))
    if len(matches) != 1:
        raise ValueError('command is not in the declared 27-command set')
    return int(matches[0])


def _commands(value):
    result = np.asarray(value)
    if result.shape != (N, 3):
        raise ValueError('commands must have five three-vectors')
    for command in result:
        command_index(command)
    return result


def encode_reports(own_observation, actual_commands, proposals, tick):
    own = np.asarray(own_observation)
    actual = _commands(actual_commands)
    proposed = _commands(proposals)
    if own.shape != (N, 3) or not np.isfinite(own).all():
        raise ValueError('only five finite own-position rows may be reported')
    if tick not in REPORT_TICKS:
        raise ValueError('report outside the delayed four-tick clock')
    xyz = np.rint(own.astype(np.float64) * (1000.0, 1000.0, 100.0) +
                  (0.0, 0.0, 50.0)).astype(np.int64)
    if np.any(xyz < LOW) or np.any(xyz > HIGH):
        raise ValueError('report position outside native bounds')
    return tuple(REPORT.pack(2, i, HOLD, 0, tick // HOLD, tick,
                             *xyz[i].tolist(), *actual[i].astype(int).tolist(),
                             *proposed[i].astype(int).tolist()) for i in range(N))


def decode_reports(packets, tick):
    if len(packets) != N or tick not in REPORT_TICKS:
        raise ValueError('wrong report count or round')
    positions = np.empty((N, 3), dtype=np.float64)
    actual = np.empty((N, 3), dtype=np.float64)
    proposed = np.empty((N, 3), dtype=np.float64)
    for i, packet in enumerate(packets):
        if len(packet) != REPORT.size:
            raise ValueError('report must contain exactly 24 bytes')
        version, agent, hold, reserved, seq, observed, *values = REPORT.unpack(packet)
        if (version, agent, hold, reserved, seq, observed) != (2, i, HOLD, 0, tick // HOLD, tick):
            raise ValueError('report identity, age or hold mismatch')
        positions[i], actual[i], proposed[i] = values[:3], values[3:6], values[6:]
    if np.any(positions < LOW) or np.any(positions > HIGH):
        raise ValueError('decoded position outside native bounds')
    _commands(actual)
    _commands(proposed)
    return positions, actual, proposed


def encode_command(mask, member, q, tick):
    mask_array(mask)
    if tick not in REPORT_TICKS or member != (tick // HOLD) % N:
        raise ValueError('command round or member mismatch')
    if not isinstance(q, (int, np.integer)) or not 0 <= q < len(COMMANDS):
        raise ValueError('invalid command index')
    return COMMAND.pack(2, int(mask), HOLD, int(member), tick // HOLD, tick + HOLD, int(q))


def decode_command(packet, tick):
    if len(packet) != COMMAND.size or tick not in REPORT_TICKS:
        raise ValueError('command must contain exactly 16 bytes at a report tick')
    version, mask, hold, member, seq, effective, q = COMMAND.unpack(packet)
    if (version, hold, member, seq, effective) != (2, HOLD, (tick // HOLD) % N,
                                                   tick // HOLD, tick + HOLD):
        raise ValueError('command identity, effective tick or hold mismatch')
    mask_array(mask)
    if q >= len(COMMANDS):
        raise ValueError('invalid command index')
    return mask, member, q


def forecast_positions(positions, actual_commands, proposals, tick, member):
    """Return candidate positions at +5..+8 after four actual prefix ticks."""
    if tick not in REPORT_TICKS or member != (tick // HOLD) % N:
        raise ValueError('forecast round or member mismatch')
    positions = np.asarray(positions, dtype=np.float64)
    actual = _commands(actual_commands)
    proposed = _commands(proposals)
    if positions.shape != (N, 3) or not np.isfinite(positions).all():
        raise ValueError('expected five finite reported positions')
    prefix = positions.copy()
    for _ in range(HOLD):
        prefix = np.clip(prefix + actual * 30.0, LOW, HIGH)
    forecast = np.empty((len(COMMANDS), HOLD, N, 3), dtype=np.float64)
    for q, command in enumerate(COMMANDS):
        candidate = proposed.copy()
        candidate[member] = command
        state = prefix.copy()
        for offset in range(HOLD):
            state = np.clip(state + candidate * 30.0, LOW, HIGH)
            forecast[q, offset] = state
    return forecast
