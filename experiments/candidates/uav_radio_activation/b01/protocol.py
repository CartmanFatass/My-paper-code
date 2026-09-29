"""Fixed public-information codecs for B01's provisioned control link."""

import struct

import numpy as np


N = 5
U = 50
HORIZON = 256
HOLD = 4
SEED = 29305000
WORLDS = 64
ALL_ON = (1 << N) - 1
REPORT = struct.Struct('<BBBBIIhhhbbb3x')
COMMAND = struct.Struct('<BBBBIII')
DEADLINE_SECONDS = 1.0 - (N * REPORT.size + COMMAND.size) * 8 / 2000.0
LOW = np.array((0.0, 0.0, 50.0))
HIGH = np.array((1000.0, 1000.0, 150.0))


def mask_array(mask):
    if not isinstance(mask, (int, np.integer)) or not 0 < mask <= ALL_ON:
        raise ValueError('expected a nonempty five-transmitter mask')
    return (int(mask) & (1 << np.arange(N))) != 0


def encode_map(site_xy):
    values = np.asarray(site_xy, dtype=np.float64)
    if values.shape != (U, 2) or not np.isfinite(values).all():
        raise ValueError('site map must be finite (50, 2) coordinates')
    if np.any(values < 0) or np.any(values > 1000):
        raise ValueError('site map outside the declared area')
    return np.rint(values).astype('<i4').tobytes()


def decode_map(payload):
    if len(payload) != 400:
        raise ValueError('site map must contain exactly 400 bytes')
    values = np.frombuffer(payload, dtype='<i4').reshape(U, 2).astype(np.float64)
    if np.any(values < 0) or np.any(values > 1000):
        raise ValueError('encoded site map outside the declared area')
    return values


def encode_reports(own_observation, commands, tick):
    own = np.asarray(own_observation)
    commands = np.asarray(commands)
    if own.shape != (N, 3) or commands.shape != (N, 3):
        raise ValueError('only own-position rows and newly chosen commands are report inputs')
    if not np.isfinite(own).all() or not np.isin(commands, (-1, 0, 1)).all():
        raise ValueError('invalid position or discrete velocity command')
    if tick not in range(0, HORIZON, HOLD):
        raise ValueError('report outside the fixed four-tick clock')
    xyz = own.astype(np.float64) * (1000.0, 1000.0, 100.0) + (0.0, 0.0, 50.0)
    xyz = np.rint(xyz).astype(np.int64)
    if np.any(xyz < LOW) or np.any(xyz > HIGH):
        raise ValueError('report position outside native bounds')
    return tuple(REPORT.pack(1, i, HOLD, 0, tick // HOLD, tick,
                             *xyz[i].tolist(), *commands[i].astype(int).tolist())
                 for i in range(N))


def decode_reports(packets, tick):
    if len(packets) != N or tick not in range(0, HORIZON, HOLD):
        raise ValueError('wrong report count or round')
    positions = np.empty((N, 3), dtype=np.float64)
    commands = np.empty((N, 3), dtype=np.float64)
    for i, packet in enumerate(packets):
        if len(packet) != REPORT.size or packet[-3:] != b'\x00' * 3:
            raise ValueError('wrong report size or reserved bytes')
        version, agent, hold, reserved, seq, observed, x, y, z, vx, vy, vz = REPORT.unpack(packet)
        if (version, agent, hold, reserved, seq, observed) != (1, i, HOLD, 0, tick // HOLD, tick):
            raise ValueError('report identity, age or hold mismatch')
        positions[i] = (x, y, z)
        commands[i] = (vx, vy, vz)
    if np.any(positions < LOW) or np.any(positions > HIGH) or not np.isin(commands, (-1, 0, 1)).all():
        raise ValueError('invalid decoded report')
    return positions, commands


def encode_command(mask, tick):
    mask_array(mask)
    if tick not in range(0, HORIZON, HOLD):
        raise ValueError('command outside the fixed clock')
    return COMMAND.pack(1, mask, HOLD, 0, tick // HOLD, tick + 1, 0)


def decode_command(packet, tick):
    if len(packet) != COMMAND.size:
        raise ValueError('mask command must contain exactly 16 bytes')
    version, mask, hold, reserved, seq, effective, padding = COMMAND.unpack(packet)
    if (version, hold, reserved, seq, effective, padding) != (1, HOLD, 0, tick // HOLD, tick + 1, 0):
        raise ValueError('command identity, time or hold mismatch')
    mask_array(mask)
    return mask


def forecast_positions(positions, commands, tick):
    """Reward after movement scores +2..+5; the final delivery scores +2..+4."""
    positions = np.array(positions, dtype=np.float64, copy=True)
    commands = np.asarray(commands, dtype=np.float64)
    if positions.shape != (N, 3) or commands.shape != (N, 3):
        raise ValueError('expected five reported positions and commands')
    offsets = tuple(range(2, min(5, HORIZON - tick) + 1))
    trajectory = []
    for offset in range(1, max(offsets) + 1):
        positions = np.clip(positions + commands * 30.0, LOW, HIGH)
        if offset in offsets:
            trajectory.append(positions.copy())
    return np.stack(trajectory), offsets
