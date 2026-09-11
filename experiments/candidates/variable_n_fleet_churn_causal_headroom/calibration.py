"""Result-blind R03 cost projection over synthetic native and solver inputs."""

from fractions import Fraction
import json
from time import perf_counter

from .solver import Option, solve_epoch

TICKS = 9_418_560
SCORED_ROWS = 738_685_168
CALLS = 376_688
CONTINUATIONS = 94_128
# Each of eight zone returns has denominator 60,80,100,120 (LCM1200).
# At any fixed class stage, baseline is a fixed shift. Each coordinate has
# at most9601 possible totals, hence a nondominated frontier has at most9601.
MAX_CREATED = 3 * 16 * 9601 * 1961
SAFETY_FACTOR = 2.0


def synthetic_solver_probe(toy=False):
    """Time exact arithmetic, sorting, map copying and scalar reductions together.

    These artificial outcomes are unrelated to any native world. The projection
    extrapolates measured complete solver cost to the finite lattice upper count;
    it is a conservative planning estimate, not a universal runtime guarantee.
    """
    width, count = (3, 2) if toy else (1961, 16)
    classes = {}
    for i in range(count):
        classes[f"synthetic-{i:02d}"] = tuple(
            Option((j, 255, 255, 255),
                   (Fraction(j % 3, 1200), Fraction(-(j % 3), 1200)),
                   j == 0)
            for j in range(width))
    start = perf_counter()
    solution = solve_epoch(0, classes)
    seconds = perf_counter() - start
    return {
        "seconds": seconds, "created": solution.stats.created,
        "retained": solution.stats.retained,
        "eliminated": solution.stats.eliminated,
        "complete": solution.stats.complete,
        "action_records": solution.stats.action_records,
        "projected_created_upper": MAX_CREATED,
        "projected_seconds": SAFETY_FACTOR * seconds * MAX_CREATED
        / solution.stats.created,
        "source": "synthetic exact fractions; no native endpoint data",
    }


def serialization_probe(toy=False):
    # A conservative 16KiB admitted-history/continuation record includes more
    # space than the three snapshots (8*38+2*15+4 doubles), BCRH inputs and masks.
    count = 2 if toy else 1961
    start = perf_counter()
    rows = [{"admitted_history": "0" * 16384,
             "physical_commands": [[255] * 4 for _ in range(6)],
             "checks": [True] * 12} for _ in range(count)]
    encoded = json.dumps(rows, sort_keys=True)
    seconds = perf_counter() - start
    return {"seconds": seconds, "records": count, "bytes": len(encoded),
            "projected_seconds": SAFETY_FACTOR * seconds * CONTINUATIONS / count,
            "basis": "synthetic 16KiB records; grouping/allocation/serialization allowance"}


def project(native, solver, serialization):
    score_unit = max(row["seconds"] / row["candidate_count"]
                     for row in native["scores"])
    tick_unit = native["ticks"]["seconds"] / native["ticks"]["count"]
    setup = SAFETY_FACTOR * native["prehistory"]["seconds"] * 96 / native["prehistory"]["calls"]
    terms = {
        "native_ticks": SAFETY_FACTOR * TICKS * tick_unit,
        "full_bcrh_rows": SAFETY_FACTOR * SCORED_ROWS * score_unit,
        "exact_solver": solver["projected_seconds"],
        "history_serialization": serialization["projected_seconds"],
        "prehistory_enumeration": setup,
        # Includes final JSON disk write and wrapper/fixture setup; no existing
        # result file is read to choose this prospectively fixed allowance.
        "fixed_setup_and_publication_allowance": 60.0,
    }
    seconds = sum(terms.values())
    return {
        "total_native_ticks_upper": TICKS,
        "full_bcrh_calls_upper": CALLS,
        "full_bcrh_scored_rows_upper": SCORED_ROWS,
        "continuations_upper": CONTINUATIONS,
        "t_tick_measured": tick_unit, "t_score_measured": score_unit,
        "safety_factor": SAFETY_FACTOR, "terms_seconds": terms,
        "projected_seconds": seconds, "cap_seconds": 2700,
        "status": "BLOCKED_WALL_CAP" if seconds >= 2700 else "CALIBRATION_BELOW_CAP",
        "native_terms_alone_exceed_cap": terms["native_ticks"] + terms["full_bcrh_rows"] >= 2700,
        "interpretation": "planning estimate only; no CI branch or scientific result",
    }
