"""Typed version-six pilot and header-only packages on the frozen RF grid."""

from __future__ import annotations

import numpy as np

from experiments.candidates.uav_radio_uncertainty.b01.protocol import (
    ALL_ON, COMMAND, COMMANDS, HIGH, LOW, REPORT_HEADER, array_digest,
    checked_codes, checked_commands, command_index, decode_map, encode_losses,
    encode_map, mask_array, report_tick, require,
)
from . import contract as c

VERSION = c.VERSION


def encode_reports(arm, own_observation, actual, proposals, tick, nav_indices,
                   loss_codes=None):
    settings = c.arm_settings(arm)
    # Reject even an opaque object without coercion, inspection or serialization.
    if arm == "P_PRIOR":
        require(loss_codes is None, "P_PRIOR forbids current-link loss codes")
    report_tick(tick)
    own = np.asarray(own_observation)
    actual, proposals = checked_commands(actual), checked_commands(proposals)
    nav = np.asarray(nav_indices)
    require(own.shape == (c.N_UAVS, 3) and np.isfinite(own).all(),
            "five normalized own-position observations required")
    require(nav.shape == (c.N_UAVS,) and nav.dtype.kind in "iu"
            and np.all((0 <= nav) & (nav <= 9)), "invalid post-C navigation state")
    codes = checked_codes(loss_codes) if arm == "P_FULL" else None
    xyz = np.rint(own.astype(np.float64) * (1000., 1000., 100.) + (0., 0., 50.))
    require(np.all((xyz >= LOW) & (xyz <= HIGH)), "reported position out of bounds")
    xyz = xyz.astype(np.int64)
    return tuple(REPORT_HEADER.pack(VERSION, i, c.HOLD, settings["delivery"],
                 tick // c.HOLD, tick, *xyz[i].tolist(),
                 *actual[i].astype(int).tolist(), *proposals[i].astype(int).tolist(),
                 int(nav[i])) + (codes[i].tobytes() if codes is not None else b"")
                 for i in range(c.N_UAVS))


def decode_reports(arm, packets, tick):
    settings = c.arm_settings(arm)
    report_tick(tick)
    require(len(packets) == c.N_UAVS, "wrong number of reports")
    positions, actual, proposed = (np.empty((c.N_UAVS, 3), dtype=np.float64) for _ in range(3))
    nav = np.empty(c.N_UAVS, dtype=np.uint8)
    codes = np.empty((c.N_UAVS, c.N_USERS), dtype=np.uint8) if arm == "P_FULL" else None
    for i, packet in enumerate(packets):
        require(len(packet) == settings["report_bytes"], "typed report size mismatch")
        version, agent, hold, delay, seq, observed, *values = REPORT_HEADER.unpack(packet[:25])
        require((version, agent, hold, delay, seq, observed) ==
                (VERSION, i, c.HOLD, settings["delivery"], tick // c.HOLD, tick),
                "report identity mismatch")
        positions[i], actual[i], proposed[i], nav[i] = values[:3], values[3:6], values[6:9], values[9]
        if codes is not None:
            codes[i] = np.frombuffer(packet[25:], dtype=np.uint8)
    require(np.all((positions >= LOW) & (positions <= HIGH)), "decoded position out of bounds")
    checked_commands(actual)
    checked_commands(proposed)
    require(np.all(nav <= 9), "decoded navigation state out of bounds")
    losses = None if codes is None else 40.0 + 0.5 * codes.astype(np.float64)
    return positions, actual, proposed, nav, losses


def encode_command(arm, mask, member, q, tick):
    settings = c.arm_settings(arm)
    report_tick(tick)
    mask_array(mask)
    require(isinstance(member, (int, np.integer)) and not isinstance(member, (bool, np.bool_))
            and member == (tick // c.HOLD) % c.N_UAVS
            and isinstance(q, (int, np.integer)) and not isinstance(q, (bool, np.bool_))
            and 0 <= q < len(COMMANDS), "invalid rotating override")
    return COMMAND.pack(VERSION, int(mask), c.HOLD, int(member), tick // c.HOLD,
                        tick + settings["delivery"], int(q))


def decode_command(arm, packet, tick):
    settings = c.arm_settings(arm)
    report_tick(tick)
    require(len(packet) == c.COMMAND_BYTES, "command must contain 16 bytes")
    version, mask, hold, member, seq, effective, q = COMMAND.unpack(packet)
    require((version, hold, member, seq, effective) ==
            (VERSION, c.HOLD, (tick // c.HOLD) % c.N_UAVS, tick // c.HOLD,
             tick + settings["delivery"]), "command identity mismatch")
    mask_array(mask)
    require(q < len(COMMANDS), "decoded override out of bounds")
    return mask, member, q
