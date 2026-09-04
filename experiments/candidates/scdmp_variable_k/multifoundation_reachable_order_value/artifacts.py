"""Create-only action-map freeze and held-out namespace fence."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Callable

from .selection import DevelopmentMapping, STATE_ROWS, TRAINING_SEEDS
from .native_state import DisturbanceHold, TapeAddress
from .rng import heldout_tape_address, materialize_disturbance_tape
from .contracts import HELDOUT_NAMESPACE_TOKEN


class ActionMapArtifactError(RuntimeError):
    pass


def freeze_action_map(
    path: str | Path,
    mapping: DevelopmentMapping,
    *,
    scratch_observer: Callable[[Path], None] | None = None,
) -> bytes:
    """Create the immutable action-map artifact before any held-out address exists."""

    if not isinstance(mapping, DevelopmentMapping):
        raise TypeError("a typed frozen mapping is required")
    destination = Path(path)
    if destination.exists():
        raise ActionMapArtifactError("development action map already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp"
        )
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(mapping.serialized_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        if scratch_observer is not None:
            scratch_observer(temporary)
        os.link(temporary, destination)
    except FileExistsError as error:
        raise ActionMapArtifactError("development action map already exists") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    observed = destination.read_bytes()
    if observed != mapping.serialized_bytes:
        raise ActionMapArtifactError("development action map direct bytes differ after freeze")
    return observed


_OPEN_CAPABILITIES: set[object] = set()


@dataclass(frozen=True, slots=True)
class HeldoutTapePermit:
    state_id: str
    address: TapeAddress
    rows: tuple[DisturbanceHold, ...]
    _capability: object


class HeldoutNamespace:
    __slots__ = ("token", "_capability")

    def __init__(self, token: str) -> None:
        self.token = token
        self._capability = object()
        _OPEN_CAPABILITIES.add(self._capability)

    def address(self, state_id: str, tape: int) -> HeldoutTapePermit:
        states = {item[0] for item in STATE_ROWS}
        if state_id not in states or tape not in range(16):
            raise ActionMapArtifactError("held-out address lies outside RUN-01")
        address = heldout_tape_address(self.token, state_id, tape)
        return HeldoutTapePermit(
            state_id, address, materialize_disturbance_tape(address), self._capability,
        )


def validate_heldout_permit(
    value: object,
) -> tuple[str, TapeAddress, tuple[DisturbanceHold, ...]]:
    if (
        not isinstance(value, HeldoutTapePermit)
        or value._capability not in _OPEN_CAPABILITIES
    ):
        raise ActionMapArtifactError("held-out evaluation requires a post-freeze permit")
    prefix = f"{HELDOUT_NAMESPACE_TOKEN}/{value.state_id}/"
    try:
        tape = int(value.address.tape_id.removeprefix(prefix))
    except ValueError as error:
        raise ActionMapArtifactError("held-out permit state/address binding differs") from error
    if (
        not value.address.tape_id.startswith(prefix)
        or value.address != heldout_tape_address(
            HELDOUT_NAMESPACE_TOKEN, value.state_id, tape,
        )
    ):
        raise ActionMapArtifactError("held-out permit state/address binding differs")
    expected = materialize_disturbance_tape(value.address)
    if value.rows != expected:
        raise ActionMapArtifactError("held-out permit tape bytes differ from its address")
    return value.state_id, value.address, value.rows


def open_heldout_namespace(
    path: str | Path, mapping: DevelopmentMapping
) -> HeldoutNamespace:
    """Open held-out addressing only after the exact direct mapping bytes persist."""

    source = Path(path)
    if not source.is_file():
        raise ActionMapArtifactError("development action map is not frozen")
    try:
        encoded = source.read_bytes()
    except OSError as error:
        raise ActionMapArtifactError("development action map cannot be read") from error
    if encoded != mapping.serialized_bytes:
        raise ActionMapArtifactError("development action map direct bytes differ")
    return HeldoutNamespace(mapping.heldout_namespace_token)


__all__ = [
    "ActionMapArtifactError", "HeldoutNamespace", "HeldoutTapePermit", "freeze_action_map",
    "open_heldout_namespace", "validate_heldout_permit",
]
