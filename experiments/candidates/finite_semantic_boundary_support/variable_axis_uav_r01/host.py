from __future__ import annotations

from itertools import product
from typing import Any

import hashlib

from .counter import address, categorical, permutation
from .oracle import accepted_receipt, denied_open_both_receipt


PRESENTATIONS = (
    (11, 0, 0, 0),
    (23, 0, 0, 1),
    (37, 0, 1, 0),
    (53, 0, 1, 1),
    (71, 1, 0, 0),
    (89, 1, 0, 1),
    (107, 1, 1, 0),
    (127, 1, 1, 1),
)
ARMS = ("AUTHENTIC", "REASSOCIATED")
DONOR_PERMUTATIONS = (
    (1, 2, 3, 0),
    (1, 3, 0, 2),
    (2, 0, 3, 1),
    (3, 0, 1, 2),
)


def _donor_permutation(key: dict[str, Any], block: int) -> tuple[int, ...]:
    coordinates: tuple[str | int, ...] = (
        key["M"],
        key["occupancy"],
        key["i"],
        key["r"],
        key["kappa"],
        key["mu"],
        key["lambda"],
        block,
    )
    index = categorical(4, key["seed"], "reassociation-permutation", coordinates)
    return DONOR_PERMUTATIONS[index]


def _worlds(key: dict[str, Any]) -> list[dict[str, Any]]:
    latent: list[dict[str, int]] = []
    for relevant_reservation in (0, 1):
        for relevant_slot, decoy_reservation in product((0, 1), repeat=2):
            latent.append(
                {
                    "world": len(latent),
                    "relevant_slot": relevant_slot,
                    "relevant_reservation": relevant_reservation,
                    "decoy_reservation": decoy_reservation,
                }
            )

    worlds: list[dict[str, Any]] = []
    for latent_world in latent:
        world_index = latent_world["world"]
        block_start = 0 if world_index < 4 else 4
        position = world_index - block_start
        if key["arm"] == "AUTHENTIC":
            donor_world = world_index
        else:
            donor_world = block_start + _donor_permutation(key, block_start // 4)[position]
        semantic_bit = latent[donor_world]["relevant_slot"]
        relevant_slot = latent_world["relevant_slot"]
        records = {
            relevant_slot: latent_world["relevant_reservation"] ^ key["mu"],
            1 - relevant_slot: latent_world["decoy_reservation"] ^ key["mu"],
        }
        transactions = [
            accepted_receipt(records, open_slot, lane_action)
            for open_slot, lane_action in product((0, 1), repeat=2)
        ]
        transactions.append(denied_open_both_receipt())
        worlds.append(
            {
                **latent_world,
                "donor_world": donor_world,
                "semantic_bit": semantic_bit,
                "surface_bit": semantic_bit ^ key["kappa"],
                "records": [
                    {"slot": slot, "payload_bit": records[slot]} for slot in (0, 1)
                ],
                "selector_view": {
                    "i": key["i"],
                    "r": key["r"],
                    "surface_bit": semantic_bit ^ key["kappa"],
                    "auth_ok": 1,
                },
                "transactions": transactions,
            }
        )
    return worlds


def _paired_address(key: dict[str, Any]) -> str:
    coordinates: tuple[str | int, ...] = (
        key["M"],
        key["occupancy"],
        key["i"],
        key["r"],
        key["kappa"],
        key["mu"],
        key["lambda"],
    )
    return hashlib.sha256(
        address(key["seed"], "paired-exogenous-world", coordinates, 0)
    ).hexdigest()


def _slot_token(seed: int, M: int, lineage: int, join_epoch: int) -> str:
    digest = hashlib.sha256(
        address(seed, "slot-token", (M, lineage, join_epoch), 0)
    ).hexdigest()
    return f"tok_{digest[:32]}"


def _ordered_pairs(seed: int, M: int, window: int, active: list[int]) -> list[list[int]]:
    order = permutation(
        len(active), seed, "window-pairing", (M, window)
    )
    shuffled = [active[index] for index in order]
    return [shuffled[index : index + 2] for index in range(0, len(shuffled), 2)]


def build_churn_fixtures() -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for M in (6, 8, 10):
        for seed, _kappa, _mu, _lambda in PRESENTATIONS:
            hidden = permutation(M, seed, "churn-hidden-permutation", (M,))
            active_sets = (
                set(range(M)),
                set(range(M)) - {hidden[0], hidden[1]},
                set(range(M)),
                set(range(M)) - {hidden[2], hidden[3]},
                set(range(M)),
            )
            state = {lineage: 0 for lineage in range(M)}
            tokens: dict[int, str] = {}
            join_epochs = {lineage: -1 for lineage in range(M)}
            previous_active: set[int] = set()
            windows: list[dict[str, Any]] = []
            for window_index, active_set in enumerate(active_sets):
                active = sorted(active_set)
                for lineage in active_set - previous_active:
                    join_epochs[lineage] += 1
                    tokens[lineage] = _slot_token(
                        seed, M, lineage, join_epochs[lineage]
                    )
                before = {str(lineage): state[lineage] for lineage in active}
                for lineage in active:
                    state[lineage] += 1
                after = {str(lineage): state[lineage] for lineage in active}
                windows.append(
                    {
                        "window": window_index,
                        "active_lineages": active,
                        "active_mask": [lineage in active_set for lineage in range(M)],
                        "state_before": before,
                        "state_after": after,
                        "slot_tokens": {
                            str(lineage): tokens[lineage] for lineage in active
                        },
                        "ordered_pairs": _ordered_pairs(
                            seed, M, window_index, active
                        ),
                    }
                )
                previous_active = active_set
            fixtures.append(
                {
                    "fixture_id": f"M{M}-seed{seed}",
                    "M": M,
                    "seed": seed,
                    "hidden_permutation": hidden,
                    "windows": windows,
                }
            )
    return fixtures


def build_strata() -> list[dict[str, Any]]:
    strata: list[dict[str, Any]] = []
    for M, occupancy, i, r, presentation, arm in product(
        (6, 8, 10),
        ("FULL", "REDUCED"),
        (0, 1),
        (0, 1),
        PRESENTATIONS,
        ARMS,
    ):
        seed, kappa, mu, lambda_ = presentation
        key = {
            "M": M,
            "occupancy": occupancy,
            "i": i,
            "r": r,
            "seed": seed,
            "kappa": kappa,
            "mu": mu,
            "lambda": lambda_,
            "arm": arm,
        }
        strata.append(
            {
                "key": key,
                "paired_address_sha256": _paired_address(key),
                "churn_fixture_id": f"M{M}-seed{seed}",
                "worlds": _worlds(key),
            }
        )
    return strata
