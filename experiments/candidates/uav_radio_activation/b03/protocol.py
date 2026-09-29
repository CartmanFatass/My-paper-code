"""Version-three reports and two-tick delivery with four-tick commitments."""

import struct

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.protocol import (
    ALL_ON, HIGH, HOLD, HORIZON, LOW, N, U, decode_map, encode_map, mask_array,
)
from experiments.candidates.uav_radio_activation.b02.protocol import command_index


SEED = 29307000
WORLDS = 64
DELIVERY = 2
DEADLINE_SECONDS = 2.0 - (N * 24 + 16) * 8 / 2000.0
REPORT = struct.Struct('<BBBBIIhhhbbbbbb')
COMMAND = struct.Struct('<BBBBIII')
REPORT_TICKS = range(0, HORIZON, HOLD)


def _report_tick(tick):
    if tick not in REPORT_TICKS:
        raise ValueError('report outside the four-tick clock')


def _commands(value):
    result = np.asarray(value)
    if result.shape != (N, 3):
        raise ValueError('commands must have five three-vectors')
    for command in result:
        command_index(command)
    return result


def encode_reports(own_observation, actual_commands, proposals, tick):
    _report_tick(tick)
    own = np.asarray(own_observation)
    actual = _commands(actual_commands)
    proposed = _commands(proposals)
    if own.shape != (N, 3) or not np.isfinite(own).all():
        raise ValueError('only five finite own-position rows may be reported')
    xyz = np.rint(own.astype(np.float64) * (1000.0, 1000.0, 100.0) +
                  (0.0, 0.0, 50.0)).astype(np.int64)
    if np.any(xyz < LOW) or np.any(xyz > HIGH):
        raise ValueError('report position outside native bounds')
    return tuple(REPORT.pack(3, i, HOLD, DELIVERY, tick // HOLD, tick,
                             *xyz[i].tolist(), *actual[i].astype(int).tolist(),
                             *proposed[i].astype(int).tolist()) for i in range(N))


def decode_reports(packets, tick):
    _report_tick(tick)
    if len(packets) != N:
        raise ValueError('wrong report count')
    positions = np.empty((N, 3), dtype=np.float64)
    actual = np.empty((N, 3), dtype=np.float64)
    proposed = np.empty((N, 3), dtype=np.float64)
    for i, packet in enumerate(packets):
        if len(packet) != REPORT.size:
            raise ValueError('report must contain exactly 24 bytes')
        version, agent, hold, delivery, seq, observed, *values = REPORT.unpack(packet)
        if (version, agent, hold, delivery, seq, observed) != (
                3, i, HOLD, DELIVERY, tick // HOLD, tick):
            raise ValueError('report identity, delivery or hold mismatch')
        positions[i], actual[i], proposed[i] = values[:3], values[3:6], values[6:]
    if np.any(positions < LOW) or np.any(positions > HIGH):
        raise ValueError('decoded position outside native bounds')
    _commands(actual)
    _commands(proposed)
    return positions, actual, proposed


def encode_command(mask, member, q, tick):
    _report_tick(tick)
    mask_array(mask)
    if member != (tick // HOLD) % N:
        raise ValueError('command member mismatch')
    if not isinstance(q, (int, np.integer)) or not 0 <= q < len(COMMANDS):
        raise ValueError('invalid command index')
    return COMMAND.pack(3, int(mask), HOLD, int(member), tick // HOLD,
                        tick + DELIVERY, int(q))


def decode_command(packet, tick):
    _report_tick(tick)
    if len(packet) != COMMAND.size:
        raise ValueError('command must contain exactly 16 bytes')
    version, mask, hold, member, seq, effective, q = COMMAND.unpack(packet)
    if (version, hold, member, seq, effective) != (
            3, HOLD, (tick // HOLD) % N, tick // HOLD, tick + DELIVERY):
        raise ValueError('command identity, effective tick or hold mismatch')
    mask_array(mask)
    if q >= len(COMMANDS):
        raise ValueError('invalid command index')
    return mask, member, q


def forecast_positions(positions, actual_commands, proposals, tick, member,
                       *, horizon=HORIZON):
    """Score candidate postmove positions at +3..+6, truncated at horizon."""
    if not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= HORIZON or horizon % HOLD:
        raise ValueError('horizon must be a four-tick multiple from 8 to 256')
    _report_tick(tick)
    if tick >= horizon or member != (tick // HOLD) % N:
        raise ValueError('forecast round or member mismatch')
    positions = np.asarray(positions, dtype=np.float64)
    actual = _commands(actual_commands)
    proposed = _commands(proposals)
    if positions.shape != (N, 3) or not np.isfinite(positions).all():
        raise ValueError('expected five finite reported positions')
    prefix = positions.copy()
    for _ in range(DELIVERY):
        prefix = np.clip(prefix + actual * 30.0, LOW, HIGH)
    length = min(HOLD, horizon - tick - DELIVERY)
    forecast = np.empty((len(COMMANDS), length, N, 3), dtype=np.float64)
    for q, command in enumerate(COMMANDS):
        candidate = proposed.copy()
        candidate[member] = command
        state = prefix.copy()
        for offset in range(length):
            state = np.clip(state + candidate * 30.0, LOW, HIGH)
            forecast[q, offset] = state
    return forecast
