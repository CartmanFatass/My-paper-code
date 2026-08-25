"""Fail-closed array contract for the TEST-only RSCF Gate A suffix fixture.

The arrays below are *fixtures*: their literals and ``case_offset`` formulas
are not registered seeds, coordinates, initializations, learned parameters,
checkpoints, episodes, rollouts, or inference inputs.  The contract is shared
by the scalar Python oracle and the C++17 CPU host so a benchmark can compare
the same materialized lanes without importing production authorization code.
"""

from __future__ import annotations

from typing import Final

import numpy as np


ABI_TAG: Final = "SGSP_RSCF_NATIVE_ABI_V1"
SUPPORTED_WIDTHS: Final = (32, 64, 128, 256)
NATIVE_THREADS: Final = 1
CONCURRENCY_LEVELS: Final = (1, 2, 4)

MAX_AGENTS: Final = 15
HORIZON: Final = 12
HIDDEN_DIM: Final = 64
FIFO_CAPACITY: Final = 4
TAPE_MODULUS: Final = 10_000

_SPECS: Final = {
    "n_agents": (np.dtype(np.int32), ()),
    "roles": (np.dtype(np.int32), (MAX_AGENTS,)),
    "origin_slot": (np.dtype(np.int32), ()),
    "focal_index": (np.dtype(np.int32), ()),
    "forced_action": (np.dtype(np.int32), ()),
    "factual_actions": (np.dtype(np.int32), (MAX_AGENTS,)),
    "initial_fifo_basin": (np.dtype(np.int32), (MAX_AGENTS, FIFO_CAPACITY)),
    "initial_fifo_time": (np.dtype(np.int32), (MAX_AGENTS, FIFO_CAPACITY)),
    "initial_previous_action": (np.dtype(np.int32), (MAX_AGENTS,)),
    "initial_previous_success": (np.dtype(np.int32), (MAX_AGENTS,)),
    "initial_hidden": (np.dtype(np.float64), (MAX_AGENTS, HIDDEN_DIM)),
    "event_times": (np.dtype(np.int32), (2, 3)),
    "action_tape": (np.dtype(np.uint32), (HORIZON, MAX_AGENTS)),
    "detection_tape": (np.dtype(np.uint32), (HORIZON, 2, 5)),
    "uplink_tape": (np.dtype(np.uint32), (HORIZON, MAX_AGENTS)),
    "base_tape": (np.dtype(np.uint32), (HORIZON, MAX_AGENTS)),
}


def legal_actions(role: int) -> tuple[int, ...]:
    """The exact r03 role masks, represented without production imports."""
    if role in (0, 1):
        return (0, 1, 5)  # SCAN, UPLINK, HOLD
    if role == 2:
        return (2, 3, 4, 5)  # LISTEN_WEST, LISTEN_EAST, FORWARD_BASE, HOLD
    raise ValueError(f"invalid fixture role {role}")


def _fail(message: str) -> None:
    raise ValueError(f"invalid SGSP RSCF Gate A fixture batch: {message}")


def validate_fixture_batch(batch: dict[str, np.ndarray], width: int | None = None) -> None:
    """Reject every noncanonical fixture representation before either host runs.

    This intentionally accepts no optional fields, implicit casts, strided
    views, NaN/inf floating payloads, unbalanced roles, or unused-lane values.
    Such rejection is part of the native ABI/cache safety fence, not a science
    validation rule.
    """
    if not isinstance(batch, dict):
        _fail("batch must be a dict")
    expected = set(_SPECS)
    actual = set(batch)
    missing, extra = expected - actual, actual - expected
    if missing or extra:
        _fail(f"keys differ; missing={sorted(missing)}, extra={sorted(extra)}")

    inferred_width: int | None = None
    for name, (dtype, tail_shape) in _SPECS.items():
        value = batch[name]
        if not isinstance(value, np.ndarray):
            _fail(f"{name} is not an ndarray")
        if value.dtype != dtype:
            _fail(f"{name} dtype={value.dtype}, expected={dtype}")
        if not value.flags.c_contiguous:
            _fail(f"{name} must be C-contiguous")
        if value.ndim != 1 + len(tail_shape):
            _fail(f"{name} rank={value.ndim}")
        if value.shape[1:] != tail_shape:
            _fail(f"{name} shape={value.shape}, expected tail={tail_shape}")
        if inferred_width is None:
            inferred_width = int(value.shape[0])
        elif value.shape[0] != inferred_width:
            _fail(f"{name} first dimension differs")
        if np.issubdtype(value.dtype, np.floating) and not bool(np.isfinite(value).all()):
            _fail(f"{name} contains non-finite values")

    assert inferred_width is not None
    if width is not None and inferred_width != width:
        _fail(f"width={inferred_width}, expected={width}")
    if inferred_width not in SUPPORTED_WIDTHS:
        _fail(f"unsupported width {inferred_width}")

    for lane in range(inferred_width):
        n = int(batch["n_agents"][lane])
        if n not in (9, 15):
            _fail(f"lane {lane}: n_agents must be 9 or 15")
        multiplicity = n // 3
        roles = batch["roles"][lane]
        if not np.array_equal(roles[:n], np.repeat(np.arange(3, dtype=np.int32), multiplicity)):
            _fail(f"lane {lane}: roles must be contiguous balanced r03 roles")
        if not np.all(roles[n:] == -1):
            _fail(f"lane {lane}: inactive role slots must be -1")
        origin = int(batch["origin_slot"][lane])
        focal = int(batch["focal_index"][lane])
        if not 0 <= origin < HORIZON:
            _fail(f"lane {lane}: origin_slot outside horizon")
        if not 0 <= focal < n:
            _fail(f"lane {lane}: focal_index outside active roster")
        forced = int(batch["forced_action"][lane])
        if forced not in legal_actions(int(roles[focal])):
            _fail(f"lane {lane}: forced action is illegal")

        factual = batch["factual_actions"][lane]
        for agent in range(n):
            if int(factual[agent]) not in legal_actions(int(roles[agent])):
                _fail(f"lane {lane}: illegal factual action at agent {agent}")
        if not np.all(factual[n:] == -1):
            _fail(f"lane {lane}: inactive factual actions must be -1")

        fifo_basin = batch["initial_fifo_basin"][lane]
        fifo_time = batch["initial_fifo_time"][lane]
        for agent in range(MAX_AGENTS):
            active = agent < n
            seen_empty = False
            for position in range(FIFO_CAPACITY):
                basin, event_time = int(fifo_basin[agent, position]), int(fifo_time[agent, position])
                empty = basin == -1 and event_time == -1
                seen_empty = seen_empty or empty
                if seen_empty and not empty:
                    _fail(f"lane {lane}: FIFO reports must be compact from the head")
                if not active and not empty:
                    _fail(f"lane {lane}: inactive FIFO payload")
                if active and roles[agent] in (0, 1) and position >= 2 and not empty:
                    _fail(f"lane {lane}: surveyor FIFO exceeds r03 capacity")
                if not empty and (basin not in (0, 1) or not 0 <= event_time < HORIZON):
                    _fail(f"lane {lane}: malformed FIFO report")
        previous_action = batch["initial_previous_action"][lane]
        previous_success = batch["initial_previous_success"][lane]
        for agent in range(MAX_AGENTS):
            if agent >= n:
                if previous_action[agent] != -1 or previous_success[agent] != 0:
                    _fail(f"lane {lane}: inactive previous-state payload")
                if not np.all(batch["initial_hidden"][lane, agent] == 0.0):
                    _fail(f"lane {lane}: inactive hidden-state payload")
            elif int(previous_action[agent]) not in (-1, 0, 1, 2, 3, 4, 5):
                _fail(f"lane {lane}: invalid previous action")
            elif int(previous_success[agent]) not in (0, 1):
                _fail(f"lane {lane}: invalid previous-success flag")

        times = batch["event_times"][lane]
        if np.any(times < 0) or np.any(times > 7) or any(len(set(map(int, row))) != 3 for row in times):
            _fail(f"lane {lane}: event times must be distinct values in [0, 7]")
        for tape_name in ("action_tape", "detection_tape", "uplink_tape", "base_tape"):
            if np.any(batch[tape_name][lane] >= TAPE_MODULUS):
                _fail(f"lane {lane}: {tape_name} exceeds fixture tape modulus")
