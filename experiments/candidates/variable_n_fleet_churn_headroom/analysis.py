"""Scientific arithmetic and exact R02 population adapter for controller headroom."""

from __future__ import annotations

import ctypes
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
from typing import Iterable, Sequence

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    _episode_input,
)
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import (
    run_headroom_fixture,
)
from scripts import run_vnfc_bpcr_r02 as r02


TARGET_SEED = 2026090311
TARGET_UPDATES = 64
TARGET_BEAM_WIDTH = 1024
MATERIAL_MARGIN = Fraction(1, 10)
OBJECT = "VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02"
_WITNESS = (
    Path(__file__).resolve().parents[3]
    / "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_CONTROLLER_HEADROOM_K256_ACCEPTED_WITNESS_20260904.json"
)


def prospective_cost(beam_width: int, world_count: int = 16) -> dict[str, object]:
    per_world = 1961 + 2 * beam_width * 1961
    total = world_count * per_world
    projected_wall = 723.80 * total / 64_289_424
    return {
        "law": "beam_expansions_per_world(K)<=1961+2*K*1961; "
        "beam_expansions_total(K)<=worlds*(1961+2*K*1961); "
        "native_ticks_total(K)<=20*beam_expansions_total(K)",
        "beam_width": beam_width,
        "world_count": world_count,
        "beam_expansions_per_world_upper_bound": per_world,
        "beam_expansions_total_upper_bound": total,
        "beam_native_ticks_total_upper_bound": 20 * total,
        "persistent_native_ticks_total_upper_bound": world_count * 1961 * 60,
        "bcrh_decision_calls": world_count * 6,
        "bcrh_scored_candidates_upper_bound": world_count * 6 * 1961,
        "result_blind_projected_wall_seconds": projected_wall,
        "projection_basis": "723.80 seconds at K=1024 over 16 frozen worlds",
        "per_invocation_wall_cap_seconds": 2700.0,
        "projection_within_wall_cap": projected_wall <= 2700.0,
    }


def regenerate_r02_world(
    *, seed: int, updates: int, purpose: str, roster_size: int,
    failed_zone: int, row: int
) -> object:
    source = r02.install_r02()
    config = source.BExploreRunConfig(source.PRIMARY_STAGE, seed, updates)
    master = source.derive_seed_master(config)["master"]
    rng = source._SeedRNG(master)
    return source._build_world(
        rng,
        config,
        purpose=purpose,
        roster_size=roster_size,
        failed_zone=failed_zone,
        row=row,
        now=datetime(2026, 9, 3, tzinfo=timezone.utc),
    )


def target_worlds() -> tuple[tuple[int, int, object], ...]:
    return tuple(
        (
            zone,
            row,
            regenerate_r02_world(
                seed=TARGET_SEED,
                updates=TARGET_UPDATES,
                purpose="heldout-N7",
                roster_size=7,
                failed_zone=zone,
                row=row,
            ),
        )
        for zone in (1, 2)
        for row in range(8)
    )


def native_fixture_bytes(fixture: object) -> bytes:
    packed = _episode_input(fixture)
    return ctypes.string_at(ctypes.byref(packed), ctypes.sizeof(packed))


def fraction_payload(value: Fraction) -> dict[str, int | float]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "binary64": float(value),
    }


def _endpoint_fraction(endpoint: object) -> Fraction:
    numerator, denominator = endpoint  # type: ignore[misc]
    return Fraction(int(numerator), int(denominator))


def accepted_k256_worlds() -> dict[tuple[int, int], dict[str, object]]:
    payload = json.loads(_WITNESS.read_text(encoding="utf-8"))
    return {
        (int(world["zone"]), int(world["row"])): world
        for world in payload["worlds"]
    }


def _witness_endpoint(value: object) -> Fraction:
    endpoint = value  # type: ignore[assignment]
    return Fraction(int(endpoint["numerator"]), int(endpoint["denominator"]))  # type: ignore[index]


def summarize_world(
    zone: int, row: int, native: dict[str, object],
    accepted: dict[str, object] | None = None,
) -> dict[str, object]:
    endpoints = native["endpoints"]  # type: ignore[assignment]
    fractions = {
        name: _endpoint_fraction(endpoint)
        for name, endpoint in endpoints.items()  # type: ignore[union-attr]
    }
    accepted_k256 = (
        _witness_endpoint(accepted["accepted_k256"]["endpoint"])  # type: ignore[index]
        if accepted is not None
        else None
    )
    candidates = [
        ("ORACLE_BEAM_FAIL60_K1024", fractions["ORACLE_BEAM_FAIL60"]),
        ("PERSIST_MAX_C60", fractions["PERSIST_MAX_C60"]),
        ("BCRH", fractions["BCRH"]),
    ]
    if accepted_k256 is not None:
        candidates.insert(1, ("ORACLE_BEAM_FAIL60_K256_ACCEPTED", accepted_k256))
    witness_name, witness_fraction = min(
        candidates,
        key=lambda item: (-item[1], candidates.index(item)),
    )
    bcrh = fractions["BCRH"]
    lower = witness_fraction - bcrh
    upper = Fraction(1) - bcrh
    bcrh_facts = native["bcrh_decisions"]  # type: ignore[assignment]
    bcrh_valid = len(bcrh_facts) == 6 and all(
        fact["scorer_checker_equal"]
        and fact["independent_enumerator_equal"]
        and fact["all_candidate_records_exact"]
        and fact["scorer_command"] == fact["checker_command"]
        and fact["candidate_digest"] == fact["checker_digest"]
        and len(fact["candidate_records"]) == fact["candidate_count"]
        and all(record["exact_match"] for record in fact["candidate_records"])
        and 0 < fact["candidate_count"] <= 1961
        for fact in bcrh_facts  # type: ignore[union-attr]
    )
    native_valid = all(
        flags["terminal"] and flags["safety"] and flags["exclusivity"]
        for flags in native["validity"].values()  # type: ignore[union-attr]
    )
    endpoint_valid = all(Fraction(0) <= value <= Fraction(1) for value in fractions.values())
    bound_valid = Fraction(0) <= lower <= upper
    nonregression = (
        accepted_k256 is None or fractions["ORACLE_BEAM_FAIL60"] >= accepted_k256
    )
    historical_baselines_equal = (
        accepted is None
        or (
            fractions["BCRH"] == _witness_endpoint(accepted["accepted_bcrh_endpoint"])
            and fractions["PERSIST_MAX_C60"]
            == _witness_endpoint(accepted["accepted_persist_endpoint"])
        )
    )
    storage = native["search_storage"]  # type: ignore[assignment]
    selector_valid = (
        storage["max_current_frontier_capacity"] <= native["beam_width"]  # type: ignore[index]
        and storage["max_next_selector_capacity"] <= native["beam_width"]  # type: ignore[index]
        and storage["max_live_nodes_high_water"] <= 2 * native["beam_width"] + 1  # type: ignore[index]
        and all(
            depth["transient"]["nodes_high_water"] <= 1
            and depth["enumerator_count_high_water"] <= 1961
            for depth in native["beam_depths"]  # type: ignore[union-attr]
        )
    )
    valid = (
        bcrh_valid
        and native_valid
        and endpoint_valid
        and bound_valid
        and nonregression
        and historical_baselines_equal
        and selector_valid
        and bool(native["persist_sensitivity_agreement"])
    )
    published_names = {
        "BCRH": "BCRH",
        "PERSIST_MAX_C60": "PERSIST_MAX_C60",
        "ORACLE_BEAM_FAIL60": "ORACLE_BEAM_FAIL60_K1024_MEMBOUND",
    }
    endpoint_payload = {
        published_names[name]: {
            "numerator": int(endpoints[name][0]),  # type: ignore[index]
            "denominator": int(endpoints[name][1]),  # type: ignore[index]
            "ratio": fraction_payload(value),
        }
        for name, value in fractions.items()
    }
    trajectories = {
        published_names[name]: trajectory
        for name, trajectory in native["trajectories"].items()  # type: ignore[union-attr]
    }
    if accepted is not None and accepted_k256 is not None:
        endpoint_payload["ORACLE_BEAM_FAIL60_K256_ACCEPTED"] = {
            "numerator": accepted_k256.numerator,
            "denominator": accepted_k256.denominator,
            "ratio": fraction_payload(accepted_k256),
        }
        trajectories["ORACLE_BEAM_FAIL60_K256_ACCEPTED"] = accepted["accepted_k256"][  # type: ignore[index]
            "complete_command_history"
        ]
    return {
        "zone": zone,
        "row": row,
        "failed_rank": native["failed_rank"],
        "endpoints": endpoint_payload,
        "measurement_complete": True,
        "search_commands": {
            published_names[name]: native["trajectories"][name][:3]  # type: ignore[index]
            for name in ("PERSIST_MAX_C60", "ORACLE_BEAM_FAIL60")
        },
        "trajectories": trajectories,
        "accepted_k256_command_history_sha256": (
            accepted["accepted_k256"]["command_history_sha256"]  # type: ignore[index]
            if accepted is not None else None
        ),
        "terminal_completion_commands": {
            published_names[name]: commands
            for name, commands in native["terminal_completion_commands"].items()  # type: ignore[union-attr]
        },
        "bcrh_decisions": bcrh_facts,
        "beam_depths": native["beam_depths"],
        "counts": native["counts"],
        "search_storage": storage,
        "witness_source": witness_name,
        "k1024_minus_accepted_k256": (
            fraction_payload(fractions["ORACLE_BEAM_FAIL60"] - accepted_k256)
            if accepted_k256 is not None else None
        ),
        "k1024_nonregression": nonregression,
        "L": fraction_payload(lower),
        "U": fraction_payload(upper),
        "individual_world_material": lower >= MATERIAL_MARGIN,
        "validity": {
            "bcrh_scorer_checker_enumerator_candidates": bcrh_valid,
            "persist_sensitivity_maximum": bool(native["persist_sensitivity_agreement"]),
            "terminal_safety_exclusivity": native_valid,
            "endpoint_unit_interval": endpoint_valid,
            "bound_order_0_le_L_le_H_le_U": bound_valid,
            "selector_conformance": selector_valid,
            "k1024_ge_accepted_k256": nonregression,
            "historical_bcrh_persist_equal": historical_baselines_equal,
            "resource": False,
            "complete": False,
            "complete_except_resource": valid,
        },
    }


def mean_fraction(values: Iterable[Fraction]) -> Fraction:
    materialized = tuple(values)
    return sum(materialized, Fraction(0)) / len(materialized)


def classify_means(
    aggregate_l: Fraction, zone_l: dict[int, Fraction]
) -> tuple[str, str]:
    if aggregate_l >= MATERIAL_MARGIN and all(zone_l[zone] >= MATERIAL_MARGIN for zone in (1, 2)):
        return "MB1024-A", "MATERIAL_PANEL_HEADROOM_WITNESSED"
    return "MB1024-D", "BOUNDED_SEARCH_REMAINS_UNRESOLVED"


def aggregate_worlds(worlds: Sequence[dict[str, object]]) -> dict[str, object]:
    if len(worlds) != 16 or any(not world["validity"]["complete"] for world in worlds):  # type: ignore[index]
        return {"branch": "MB1024-INCOMPLETE", "reason": "missing_or_invalid_world"}
    lower = {id(world): Fraction(world["L"]["numerator"], world["L"]["denominator"]) for world in worlds}  # type: ignore[index]
    upper = {id(world): Fraction(world["U"]["numerator"], world["U"]["denominator"]) for world in worlds}  # type: ignore[index]
    aggregate_l = mean_fraction(lower[id(world)] for world in worlds)
    aggregate_u = mean_fraction(upper[id(world)] for world in worlds)
    zone_l = {
        zone: mean_fraction(lower[id(world)] for world in worlds if world["zone"] == zone)
        for zone in (1, 2)
    }
    zone_u = {
        zone: mean_fraction(upper[id(world)] for world in worlds if world["zone"] == zone)
        for zone in (1, 2)
    }
    code, label = classify_means(aggregate_l, zone_l)
    return {
        "branch": code,
        "label": label,
        "material_margin": fraction_payload(MATERIAL_MARGIN),
        "zone_localized_witness": sum(
            zone_l[zone] >= MATERIAL_MARGIN for zone in (1, 2)
        ) == 1,
        "aggregate": {"L_mean": fraction_payload(aggregate_l), "U_mean": fraction_payload(aggregate_u)},
        "zones": {
            str(zone): {"L_mean": fraction_payload(zone_l[zone]), "U_mean": fraction_payload(zone_u[zone])}
            for zone in (1, 2)
        },
    }


def analyze_fixtures(
    fixtures: Sequence[tuple[int, int, object]], beam_width: int
) -> tuple[dict[str, object], ...]:
    accepted = accepted_k256_worlds()
    return tuple(
        summarize_world(
            zone, row, run_headroom_fixture(fixture, beam_width),
            accepted.get((zone, row)),
        )
        for zone, row, fixture in fixtures
    )
