"""Version-four shared reports: post-C waypoint state and two-tick delivery."""

import struct

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b03.protocol import (
    ALL_ON, HIGH, HOLD, HORIZON, LOW, N, U, DELIVERY, command_index,
    decode_map, encode_map, forecast_positions, mask_array,
)


VERSION = 4
REPORT = struct.Struct('<BBBBIIhhhbbbbbbB')
COMMAND = struct.Struct('<BBBBIII')
DEADLINE_SECONDS = 2. - (N * REPORT.size + COMMAND.size) * 8 / 2000.


def report_tick(tick):
    if not isinstance(tick, (int, np.integer)) or tick not in range(0, HORIZON, HOLD):
        raise ValueError('report outside the four-tick clock')


def commands(value):
    result = np.asarray(value)
    if result.shape != (N, 3):
        raise ValueError('commands must have five three-vectors')
    for command in result:
        command_index(command)
    return result


def navigation(value):
    result = np.asarray(value)
    if result.shape != (N,) or result.dtype.kind not in 'iu' or np.any((result < 0) | (result > 9)):
        raise ValueError('post-C waypoint indices must be five integers in0..9')
    return result.astype(np.uint8)


def encode_reports(own_observation, actual_commands, proposals, tick, nav_indices):
    report_tick(tick)
    own = np.asarray(own_observation)
    actual, proposed, nav = commands(actual_commands), commands(proposals), navigation(nav_indices)
    if own.shape != (N, 3) or not np.isfinite(own).all():
        raise ValueError('only five finite own-position rows may be reported')
    xyz = np.rint(own.astype(np.float64) * (1000., 1000., 100.) + (0., 0., 50.)).astype(np.int64)
    if np.any(xyz < LOW) or np.any(xyz > HIGH):
        raise ValueError('report position outside native bounds')
    return tuple(REPORT.pack(VERSION, i, HOLD, DELIVERY, tick // HOLD, tick,
                             *xyz[i].tolist(), *actual[i].astype(int).tolist(),
                             *proposed[i].astype(int).tolist(), int(nav[i])) for i in range(N))


def decode_reports(packets, tick):
    report_tick(tick)
    if len(packets) != N:
        raise ValueError('wrong report count')
    positions, actual, proposed = (np.empty((N, 3), dtype=np.float64) for _ in range(3))
    nav = np.empty(N, dtype=np.uint8)
    for i, packet in enumerate(packets):
        if len(packet) != REPORT.size:
            raise ValueError('report must contain exactly25bytes')
        version, agent, hold, delivery, seq, observed, *values = REPORT.unpack(packet)
        if (version, agent, hold, delivery, seq, observed) != (VERSION, i, HOLD, DELIVERY, tick // HOLD, tick):
            raise ValueError('report identity, delivery or hold mismatch')
        positions[i], actual[i], proposed[i], nav[i] = values[:3], values[3:6], values[6:9], values[9]
    if np.any(positions < LOW) or np.any(positions > HIGH):
        raise ValueError('decoded position outside native bounds')
    commands(actual)
    commands(proposed)
    navigation(nav)
    return positions, actual, proposed, nav


def encode_command(mask, member, q, tick):
    report_tick(tick)
    mask_array(mask)
    if member != (tick // HOLD) % N or not isinstance(q, (int, np.integer)) or not 0 <= q < len(COMMANDS):
        raise ValueError('invalid rotating member or command index')
    return COMMAND.pack(VERSION, int(mask), HOLD, int(member), tick // HOLD, tick + DELIVERY, int(q))


def decode_command(packet, tick):
    report_tick(tick)
    if len(packet) != COMMAND.size:
        raise ValueError('command must contain exactly16bytes')
    version, mask, hold, member, seq, effective, q = COMMAND.unpack(packet)
    if (version, hold, member, seq, effective) != (VERSION, HOLD, (tick // HOLD) % N, tick // HOLD, tick + DELIVERY):
        raise ValueError('command identity, effective tick or hold mismatch')
    mask_array(mask)
    if q >= len(COMMANDS):
        raise ValueError('invalid command index')
    return mask, member, q
