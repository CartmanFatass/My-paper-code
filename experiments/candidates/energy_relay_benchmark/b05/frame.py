"""SW spawn-corner canonical frame of ``b05_canonical_frame_a01`` (energy_relay_benchmark).

The G4 = {IDENTITY, MIRROR_X, MIRROR_Y, ROT180} subgroup of D4 acts on the S7-S2 observation,
state and action through DM4's reviewed adapter
``experiments/candidates/uav_geometric_generalization/b01/symmetry.py`` (imported, not copied).
``sw_frame`` chooses one element per episode from the legal reset observation so that the
team's spawn corner maps to the south-west (x < .5, y < .5 in area units); the caller holds it
to the episode end.  It mirrors DM4's ``northeast_frame`` (``b01/study.py``) with SW as target.

Physical -> canonical coordinates are ``transform_observations`` / ``transform_state``; the
policy's canonical action goes back to the physical frame with ``inverse_actions``.  Every G4
element is an involution, so the inverse is the element itself.  The absolute xy entries are
mapped ``x -> 1 - x`` in float32, which is not bitwise invertible, so callers keep the
original physical arrays for every physical consumer and never rebuild them from the
canonical copy.  IDENTITY never calls the adapter (plain copies), so an identity episode is
bitwise the plain path.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from experiments.candidates.uav_geometric_generalization.b01 import symmetry as _symmetry
from experiments.candidates.uav_geometric_generalization.b01.symmetry import (
    D4, IDENTITY, MIRROR_X, MIRROR_Y, ROT180, inverse_actions, transform_actions,
    transform_observations, transform_state,
)

ROOT = Path(__file__).resolve().parents[4]
G4 = (IDENTITY, MIRROR_X, MIRROR_Y, ROT180)
AREA_CENTRE = 0.5   # own xy entries 0-1 are x/area, y/area (routed_core.py 3965-3969)
# Spawn corner of the team-mean legal own xy -> the element that maps it to SW.
CORNER_ELEMENT = {"W,S": IDENTITY, "W,N": MIRROR_Y, "E,S": MIRROR_X, "E,N": ROT180}
ADAPTER_PATH = Path(_symmetry.__file__).resolve()


def corner_of(mean_xy, centre: float = AREA_CENTRE) -> str:
    """"W,S" / "W,N" / "E,S" / "E,N" of a team-mean xy (W/S = strictly below ``centre``)."""
    x, y = float(mean_xy[0]), float(mean_xy[1])
    return f"{'W' if x < centre else 'E'},{'S' if y < centre else 'N'}"


def spawn_corner(observations) -> str:
    """Corner of the legal team-mean own xy (obs entries 0-1, area units) of one step."""
    return corner_of(np.asarray(observations)[:, :2].mean(axis=0))


def sw_frame(observations) -> D4:
    """G4 element mapping the team's spawn corner to SW, from the reset observation (8, 365).

    W,S (x < .5, y < .5) -> IDENTITY; W,N (x < .5, y >= .5) -> MIRROR_Y (y -> 1 - y: N -> S);
    E,S (x >= .5, y < .5) -> MIRROR_X (x -> 1 - x: E -> W); E,N -> ROT180 (both: NE -> SW).
    DM4's ``northeast_frame`` is the same rule with NE as target (W,S -> ROT180, W,N -> MIRROR_X,
    E,S -> MIRROR_Y, E,N -> IDENTITY).
    """
    return CORNER_ELEMENT[spawn_corner(observations)]


def canonical_inputs(observations, state, frame: D4):
    """(observations, state) in ``frame``; IDENTITY returns plain copies (no adapter call)."""
    if frame == IDENTITY:
        return np.array(observations, copy=True), np.array(state, copy=True)
    return transform_observations(observations, frame), transform_state(state, frame)


def canonical_observations(observations, frame: D4):
    if frame == IDENTITY:
        return np.array(observations, copy=True)
    return transform_observations(observations, frame)


def canonical_state(state, frame: D4):
    if frame == IDENTITY:
        return np.array(state, copy=True)
    return transform_state(state, frame)


def physical_actions(actions, frame: D4):
    """Canonical (8, 4) action -> physical frame (xy only; z and dock unchanged)."""
    if frame == IDENTITY:
        return np.array(actions, copy=True)
    return inverse_actions(actions, frame)


def canonical_actions(actions, frame: D4):
    """Physical (8, 4) action -> canonical frame (tests and readers)."""
    if frame == IDENTITY:
        return np.array(actions, copy=True)
    return transform_actions(actions, frame)


def full_horizontal(actions):
    """C_SW_FULL: non-zero horizontal components rescaled to unit norm; z and dock unchanged.

    The norm is invariant under G4, so rescaling after the inverse transform equals rescaling in
    the canonical frame; it is applied to the physical proposal right before the shield.
    """
    actions = np.asarray(actions)
    result = np.array(actions, copy=True)
    xy = actions[:, :2].astype(np.float64)
    norm = np.linalg.norm(xy, axis=-1)
    moving = norm > 0.0
    xy[moving] = xy[moving] / norm[moving][:, None]
    result[:, :2] = xy.astype(result.dtype)
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def adapter_record() -> dict:
    """The adapter file and the frame rule, for config/record/manifest files."""
    try:
        relative = ADAPTER_PATH.relative_to(ROOT).as_posix()
    except ValueError:
        relative = str(ADAPTER_PATH)
    return {
        "rule": "sw",
        "group": "G4 = {IDENTITY, MIRROR_X, MIRROR_Y, ROT180} (not full D4)",
        "selector": ("legal team-mean own xy (obs entries 0-1, area units) at episode reset; "
                     "W = x < .5, S = y < .5"),
        "elements": {corner: element.name for corner, element in CORNER_ELEMENT.items()},
        "held": "chosen at every lane reset, held to the episode end; all agents share it",
        "physical_side": ("shield (apply_feedback), guard and env.step receive physical-frame "
                          "observations and actions; proposals are inverse-transformed before "
                          "the shield"),
        "adapter": relative, "adapter_sha256": _sha256(ADAPTER_PATH),
    }
