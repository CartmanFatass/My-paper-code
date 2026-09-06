"""Zero-learner INDEPENDENT-NEAREST executability/cost measurement for B01."""

from __future__ import annotations

from pathlib import Path
import time

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    INDEPENDENT_NEAREST,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import (
    EpisodeCoordinate,
    execute_scripted_batch,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    TRAINING_CELLS,
)

from .study import (
    PREPARATION_KEY_ASCII,
    directory_bytes,
    make_semantic_rng,
    peak_rss_bytes,
    process_cpu_seconds,
    scenario_row,
    seed_root_key,
    write_json,
)

MAX_EPISODES = 64
MAX_WALL_SECONDS = 300.0
EPISODES_PER_CELL = 8


def refuse_over_cap(*, episodes: int, wall_cap: float) -> None:
    if episodes > MAX_EPISODES:
        raise ValueError(
            f"executability refuses more than {MAX_EPISODES} episodes (got {episodes})"
        )
    if wall_cap > MAX_WALL_SECONDS:
        raise ValueError(
            f"executability refuses a wall cap above {MAX_WALL_SECONDS} s (got {wall_cap})"
        )


def run_executability(
    *,
    out: Path,
    wall_cap: float = MAX_WALL_SECONDS,
    cells: tuple[str, ...] = TRAINING_CELLS,
    episodes_per_cell: int = EPISODES_PER_CELL,
) -> dict[str, object]:
    """One 8-episode batch per preparation cell; HMAC key is the preparation sub-key.

    Preparation scenarios use TRAINING_CELLS names (inside the frozen inventory
    that _parse_cell accepts) and the distinct sub-key
    ``.../seed/17/preparation``. Held-out evaluation uses HELDOUT_CELLS and the
    main seed-17 block digest, so this measurement is not the held-out panel.
    """

    episode_count = len(cells) * episodes_per_cell
    refuse_over_cap(episodes=episode_count, wall_cap=wall_cap)
    if episodes_per_cell not in (1, 8, 32):
        raise ValueError("executability batch width must be a supported native width")
    started = time.perf_counter()
    cpu0 = process_cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_semantic_rng(key_ascii=PREPARATION_KEY_ASCII)
    batches: list[dict[str, object]] = []
    scenarios: list[dict[str, object]] = []
    status = "COMPLETE"
    stop_reason = None
    for cell in cells:
        if time.perf_counter() - started > wall_cap:
            status = "TECHNICAL_STOP"
            stop_reason = "wall_cap"
            break
        coordinates = tuple(
            EpisodeCoordinate(rng.block_index, cell, row, row)
            for row in range(episodes_per_cell)
        )
        batch_started = time.perf_counter()
        rss_before = peak_rss_bytes()
        episodes = execute_scripted_batch(INDEPENDENT_NEAREST, rng, coordinates)
        batch_wall = time.perf_counter() - batch_started
        taus = [float(item.tau) for item in episodes]
        us = [float(item.U) for item in episodes]
        fs = [float(item.F) for item in episodes]
        batches.append(
            {
                "cell": cell,
                "episodes": len(episodes),
                "ticks": len(episodes) * 64,
                "wall_seconds": batch_wall,
                "peak_rss_bytes": peak_rss_bytes(),
                "rss_before": rss_before,
                "tau_mean": sum(taus) / len(taus),
                "U_mean": sum(us) / len(us),
                "F_mean": sum(fs) / len(fs),
                "Y": None,
            }
        )
        for coordinate, episode in zip(coordinates, episodes):
            scenarios.append(
                scenario_row(cell, coordinate.update_or_scenario, INDEPENDENT_NEAREST, episode)
            )
        if time.perf_counter() - started > wall_cap:
            status = "TECHNICAL_STOP"
            stop_reason = "wall_cap"
            break
    summary = {
        "object": "RCLE-TBCFV-B01-PERSIST-VS-FLEX",
        "mode": "executability",
        "status": status,
        "stop_reason": stop_reason,
        "package": INDEPENDENT_NEAREST,
        "preparation_key_ascii": PREPARATION_KEY_ASCII,
        "preparation_root_key_hex": seed_root_key(PREPARATION_KEY_ASCII).hex(),
        "block_digest_hex": authority.root_digest,
        "native": authority.certificate["native"],
        "cells": list(cells),
        "episodes_per_cell": episodes_per_cell,
        "episode_count": len(scenarios),
        "tick_count": len(scenarios) * 64,
        "batches": batches,
        "scenarios": scenarios,
        "Y_note": "ScriptedEpisodeResult has no Y; native endpoint_y is not returned",
        "wall_seconds": time.perf_counter() - started,
        "process_cpu_seconds": process_cpu_seconds() - cpu0,
        "peak_rss_bytes": peak_rss_bytes(),
        "scratch_bytes": None,
        "wall_cap": wall_cap,
        "non_learning_host_exposure": True,
    }
    write_json(out / "summary.json", summary)
    summary["scratch_bytes"] = directory_bytes(out)
    write_json(out / "summary.json", summary)
    return summary
