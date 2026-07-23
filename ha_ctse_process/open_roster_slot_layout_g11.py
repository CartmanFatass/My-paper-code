"""Isomorphic dense, permuted and sparse lifecycle-slot layouts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Callable

import numpy as np

from ha_ctse_process.dynamic_roster_testbed import HORIZON
from ha_ctse_process.open_roster_high_churn_g9 import (
    ChurnEvent,
    ChurnLedger,
    ChurnProfile,
    HighChurnEnv,
)
from ha_ctse_process.open_roster_scale_churn_g10 import (
    OSCILLATING_SCALE_CHURN_PROFILE,
    make_oscillating_scale_churn_ledger,
)


LOGICAL_CAPACITY = 48


@dataclass(frozen=True)
class SlotLayout:
    name: str
    capacity: int
    logical_to_physical: tuple[int, ...]

    def validate(self) -> None:
        if len(self.logical_to_physical) != LOGICAL_CAPACITY:
            raise ValueError("slot layout must map every logical lifecycle")
        if len(set(self.logical_to_physical)) != LOGICAL_CAPACITY:
            raise ValueError("slot layout mapping is not injective")
        if any(
            key < 0 or key >= self.capacity for key in self.logical_to_physical
        ):
            raise ValueError("slot layout mapping exceeds capacity")

    def map_keys(self, keys: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(self.logical_to_physical[key] for key in keys)


DENSE_LAYOUT = SlotLayout("dense48", 48, tuple(range(48)))
REVERSE_LAYOUT = SlotLayout("reverse48", 48, tuple(reversed(range(48))))
SPARSE_LAYOUT = SlotLayout("sparse96", 96, tuple(2 * key + 1 for key in range(48)))
PADDED_LAYOUT = SlotLayout(
    "affine_padded128",
    128,
    tuple((37 * key + 11) % 128 for key in range(48)),
)
LAYOUTS = (DENSE_LAYOUT, REVERSE_LAYOUT, SPARSE_LAYOUT, PADDED_LAYOUT)
LAYOUT_BY_NAME = {layout.name: layout for layout in LAYOUTS}


def remap_profile(profile: ChurnProfile, layout: SlotLayout) -> ChurnProfile:
    layout.validate()
    mapped = ChurnProfile(
        name=f"{profile.name}__{layout.name}",
        initial_join=layout.map_keys(profile.initial_join),
        events=tuple(
            ChurnEvent(
                event.time,
                temporarily_left=layout.map_keys(event.temporarily_left),
                rejoined=layout.map_keys(event.rejoined),
                joined=layout.map_keys(event.joined),
                terminally_left=layout.map_keys(event.terminally_left),
            )
            for event in profile.events
        ),
        capacity=layout.capacity,
        maximum_active_count=profile.maximum_active_count,
    )
    mapped.validate()
    return mapped


def _remap_table(values: np.ndarray, layout: SlotLayout) -> np.ndarray:
    source = np.asarray(values)
    if source.shape != (HORIZON, LOGICAL_CAPACITY):
        raise ValueError("logical priority table shape mismatch")
    result = np.zeros((HORIZON, layout.capacity), dtype=source.dtype)
    for logical, physical in enumerate(layout.logical_to_physical):
        result[:, physical] = source[:, logical]
    return result


def make_layout_ledger(
    episode_id: int,
    *,
    master_seed: int,
    layout: SlotLayout,
) -> ChurnLedger:
    layout.validate()
    logical = make_oscillating_scale_churn_ledger(
        episode_id, master_seed=master_seed
    )
    if logical.profile != OSCILLATING_SCALE_CHURN_PROFILE:
        raise RuntimeError("logical G10 profile identity changed")
    ledger = ChurnLedger(
        episode_id=logical.episode_id,
        master_seed=logical.master_seed,
        profile=remap_profile(logical.profile, layout),
        wave_arrivals=logical.wave_arrivals,
        owner_priorities=_remap_table(logical.owner_priorities, layout),
        presentation_priorities=_remap_table(
            logical.presentation_priorities, layout
        ),
        direct_frontier_priorities=_remap_table(
            logical.direct_frontier_priorities, layout
        ),
    )
    ledger.validate()
    return ledger


def make_layout_factory(
    layout: SlotLayout,
) -> Callable[..., ChurnLedger]:
    return partial(make_layout_ledger, layout=layout)


def pad_position_uniforms(
    logical_uniforms: np.ndarray,
    layout: SlotLayout,
) -> np.ndarray:
    values = np.asarray(logical_uniforms)
    if values.ndim != 3 or values.shape[0] != HORIZON or values.shape[2] != LOGICAL_CAPACITY:
        raise ValueError("logical uniform table shape mismatch")
    result = np.zeros(
        (values.shape[0], values.shape[1], layout.capacity),
        dtype=values.dtype,
    )
    # DirectPrimitiveARPolicy consumes sampling uniforms by autoregressive
    # token position, not by focal lifecycle key.  Layout isomorphism therefore
    # retains the first 48 position draws and only pads unused later positions.
    result[:, :, :LOGICAL_CAPACITY] = values
    return result


ENVIRONMENT_FACTORY = HighChurnEnv
