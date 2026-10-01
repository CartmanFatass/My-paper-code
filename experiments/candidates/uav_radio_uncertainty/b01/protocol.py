"""RF report version five; no inherited two-tick delivery constant."""

from __future__ import annotations

import hashlib
import struct

import numpy as np

from experiments.candidates.uav_radio_activation.b01.protocol import decode_map, encode_map
from . import contract as c

VERSION = 5
REPORT_HEADER = struct.Struct("<BBBBIIhhhbbbbbbB")
COMMAND = struct.Struct("<BBBBIII")
ALL_ON = (1 << c.N_UAVS) - 1
LOW = np.array((0.0, 0.0, c.MIN_HEIGHT))
HIGH = np.array((c.AREA_METRES, c.AREA_METRES, c.MAX_HEIGHT))
COMMANDS = np.array(c.COMMAND_GRID, dtype=np.float32)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def report_tick(tick, horizon=c.HORIZON):
    require(isinstance(tick, (int, np.integer)) and not isinstance(tick, (bool, np.bool_))
            and tick in range(0, horizon, c.HOLD), "invalid report boundary")


def mask_array(mask):
    require(isinstance(mask, (int, np.integer)) and not isinstance(mask, (bool, np.bool_))
            and 0 < int(mask) <= ALL_ON, "nonempty five-UAV mask required")
    return (int(mask) & (1 << np.arange(c.N_UAVS))) != 0


def command_index(command):
    q = np.asarray(command)
    require(q.shape == (3,) and np.isfinite(q).all(), "invalid motion command")
    matches = np.flatnonzero(np.all(COMMANDS == q, axis=1))
    require(matches.size == 1, "motion command outside the frozen grid")
    return int(matches[0])


def checked_commands(commands):
    values = np.asarray(commands)
    require(values.shape == (c.N_UAVS, 3) and np.isfinite(values).all()
            and np.isin(values, (-1, 0, 1)).all(), "five grid commands required")
    return values


def encode_losses(losses):
    values = np.asarray(losses, dtype=np.float64)
    require(values.shape == (c.N_UAVS, c.N_USERS) and np.isfinite(values).all(),
            "finite current loss matrix required")
    rounded = np.rint((values - 40.0) / 0.5)
    low, high = rounded < 0, rounded > 255
    codes = np.clip(rounded, 0, 255).astype(np.uint8)
    return codes, {"clipped_low": low, "clipped_high": high,
                   "edge_low": codes == 0, "edge_high": codes == 255}


def checked_codes(codes):
    codes = np.asarray(codes)
    require(codes.shape == (c.N_UAVS, c.N_USERS) and codes.dtype == np.uint8,
            "uint8 current-link codes required")
    return codes


def encode_reports(own_observation, actual, proposals, tick, nav_indices, loss_codes):
    report_tick(tick)
    own = np.asarray(own_observation)
    actual, proposals = checked_commands(actual), checked_commands(proposals)
    nav = np.asarray(nav_indices)
    require(own.shape == (c.N_UAVS, 3) and np.isfinite(own).all(),
            "five normalized own-position observations required")
    require(nav.shape == (c.N_UAVS,) and nav.dtype.kind in "iu"
            and np.all((0 <= nav) & (nav <= 9)), "invalid post-C navigation state")
    codes = checked_codes(loss_codes)
    xyz = np.rint(own.astype(np.float64) * (1000., 1000., 100.) + (0., 0., 50.))
    require(np.all((xyz >= LOW) & (xyz <= HIGH)), "reported position out of bounds")
    xyz = xyz.astype(np.int64)
    return tuple(REPORT_HEADER.pack(VERSION, i, c.HOLD, c.DELIVERY, tick // c.HOLD, tick,
                 *xyz[i].tolist(), *actual[i].astype(int).tolist(),
                 *proposals[i].astype(int).tolist(), int(nav[i])) + codes[i].tobytes()
                 for i in range(c.N_UAVS))


def decode_reports(packets, tick):
    report_tick(tick)
    require(len(packets) == c.N_UAVS, "wrong number of reports")
    positions, actual, proposed = (np.empty((c.N_UAVS, 3), dtype=np.float64) for _ in range(3))
    nav = np.empty(c.N_UAVS, dtype=np.uint8)
    codes = np.empty((c.N_UAVS, c.N_USERS), dtype=np.uint8)
    for i, packet in enumerate(packets):
        require(len(packet) == c.REPORT_BYTES, "RF report must contain 75 bytes")
        version, agent, hold, delay, seq, observed, *values = REPORT_HEADER.unpack(packet[:25])
        require((version, agent, hold, delay, seq, observed) ==
                (VERSION, i, c.HOLD, c.DELIVERY, tick // c.HOLD, tick), "report identity mismatch")
        positions[i], actual[i], proposed[i], nav[i] = values[:3], values[3:6], values[6:9], values[9]
        codes[i] = np.frombuffer(packet[25:], dtype=np.uint8)
    require(np.all((positions >= LOW) & (positions <= HIGH)), "decoded position out of bounds")
    checked_commands(actual)
    checked_commands(proposed)
    require(np.all(nav <= 9), "decoded navigation state out of bounds")
    return positions, actual, proposed, nav, 40.0 + 0.5 * codes.astype(np.float64)


def encode_command(mask, member, q, tick):
    report_tick(tick)
    mask_array(mask)
    require(member == (tick // c.HOLD) % c.N_UAVS and isinstance(q, (int, np.integer))
            and 0 <= q < len(COMMANDS), "invalid rotating override")
    return COMMAND.pack(VERSION, int(mask), c.HOLD, member, tick // c.HOLD,
                        tick + c.DELIVERY, int(q))


def decode_command(packet, tick):
    report_tick(tick)
    require(len(packet) == c.COMMAND_BYTES, "command must contain 16 bytes")
    version, mask, hold, member, seq, effective, q = COMMAND.unpack(packet)
    require((version, hold, member, seq, effective) ==
            (VERSION, c.HOLD, (tick // c.HOLD) % c.N_UAVS, tick // c.HOLD,
             tick + c.DELIVERY), "command identity mismatch")
    mask_array(mask)
    require(q < len(COMMANDS), "decoded override out of bounds")
    return mask, member, q


def array_digest(*values):
    """Typed, shaped, ordered hash; this is evidence, never a policy feature."""
    digest = hashlib.sha256()
    for value in values:
        array = np.ascontiguousarray(value)
        require(not array.dtype.hasobject, "object arrays cannot be evidence")
        digest.update(array.dtype.str.encode("ascii") + b"\0")
        digest.update(repr(array.shape).encode("ascii") + b"\0")
        digest.update(array.tobytes())
    return digest.hexdigest()
