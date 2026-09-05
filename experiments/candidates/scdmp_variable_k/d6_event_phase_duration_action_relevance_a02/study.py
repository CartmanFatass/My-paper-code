"""A02 fixed event-phase population, paired census and publication."""

from __future__ import annotations

from pathlib import Path
import time

from .native import (
    A02_ROOT_SEED,
    CLOCKS,
    COUNTDOWNS,
    GRAPHS,
    HORIZON,
    Host,
    SOURCE_DOMAINS,
    SOURCE_TICKS,
)
from .rng import materialize_tape
from .rule import decide_branch


COUNT_FIELDS = (
    "safe_dock", "timeout", "failure", "cable_overload", "gantry_contact",
    "attitude_loss", "formation_loss",
)
EXPECTED_LATENCY = {(7, 7): 0, (7, 13): 6, (78, 7): 6, (78, 13): 0}


def _rule(
    *,
    resource_ready: bool = True,
    integrity_valid: bool = True,
    population_established: bool = True,
    k7: int = 0,
    k78: int = 0,
    n7_plus: int = 0,
    n7_minus: int = 0,
    n78_minus: int = 0,
    n78_plus: int = 0,
    all_zero: bool = False,
) -> str:
    return decide_branch(
        resource_ready=resource_ready,
        integrity_valid=integrity_valid,
        population_established=population_established,
        k7=k7,
        k78=k78,
        n7_plus=n7_plus,
        n7_minus=n7_minus,
        n78_minus=n78_minus,
        n78_plus=n78_plus,
        all_zero=all_zero,
    )


def _stopped(
    *,
    reason: str,
    counts: dict[str, int],
    population_established: bool,
    integrity_valid: bool,
    terminal_counts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    counts["native_transitions"] = (
        counts["source_transitions"] + counts["candidate_transitions"]
    )
    counts["native_missions"] = counts["source_trajectories"] + counts["candidate_missions"]
    return {
        "branch": _rule(
            integrity_valid=integrity_valid,
            population_established=population_established,
        ),
        "integrity_valid": integrity_valid,
        "population_established": population_established,
        "reason": reason,
        "counts": counts,
        "partial_terminal_counts": terminal_counts or [],
        "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
    }


def _terminal_rows(
    groups: dict[tuple[str, int, int, str], dict[str, int]],
) -> list[dict[str, object]]:
    return [
        {
            "base_state": key[0], "countdown": key[1], "clock": key[2],
            "graph": key[3], "missions": sum(
                value[field] for field in ("safe_dock", "timeout", "failure")
            ),
            **value,
        }
        for key, value in groups.items()
    ]


def run_census(host: Host, *, deadline: float, clock=time.perf_counter) -> dict[str, object]:
    states, source = host.source_population(deadline=deadline, clock=clock)
    counts = {
        "source_trajectories": int(source["source_trajectories"]),
        "source_renewals": int(source["source_renewals"]),
        "source_transitions": int(source["source_transitions"]),
        "candidate_missions": 0,
        "candidate_renewals": 0,
        "candidate_transitions": 0,
        "evaluator_calls": 0,
        "models": 0,
        "training_datasets": 0,
        "optimizer_updates": 0,
        "adamw_steps": 0,
        "learner_evaluations": 0,
    }
    if source["cap_crossed"]:
        return _stopped(
            reason=str(source["reason"]), counts=counts,
            population_established=False, integrity_valid=False,
        )
    if source["execution_error"]:
        return _stopped(
            reason=str(source["reason"]), counts=counts,
            population_established=False, integrity_valid=False,
        )
    if not source["established"]:
        return _stopped(
            reason=str(source["reason"]), counts=counts,
            population_established=False, integrity_valid=True,
        )

    # Every one of the 6x16 primitive-addressed tapes exists before an endpoint is read.
    tapes = host.materialize_evaluation_tapes(states, seed=A02_ROOT_SEED)
    endpoints: list[dict[str, object]] = []
    terminal_groups: dict[tuple[str, int, int, str], dict[str, int]] = {}
    for state_index, state in enumerate(states):
        for countdown in COUNTDOWNS:
            for clock_k in CLOCKS:
                for graph in GRAPHS:
                    group_key = (str(state["base_state"]), countdown, clock_k, graph)
                    terminal_groups[group_key] = {field: 0 for field in COUNT_FIELDS}
                    for tape_index in range(16):
                        try:
                            result = host.mission(
                                state, countdown=countdown, clock_k=clock_k, graph=graph,
                                tape=tapes[(state_index, tape_index)],
                            )
                        except Exception as error:
                            return _stopped(
                                reason=f"candidate mission execution failed: {error}",
                                counts=counts, population_established=True,
                                integrity_valid=False,
                                terminal_counts=_terminal_rows(terminal_groups),
                            )
                        counts["candidate_missions"] += 1
                        counts["evaluator_calls"] += 1
                        counts["candidate_renewals"] += int(result["renewals"])
                        counts["candidate_transitions"] += int(result["transitions"])
                        for field in COUNT_FIELDS:
                            terminal_groups[group_key][field] += int(result[field])
                        if not result["event_applied"]:
                            return _stopped(
                                reason=(
                                    f"{state['base_state']} terminated before its countdown "
                                    f"{countdown} event or the event could not be applied"
                                ),
                                counts=counts, population_established=False,
                                integrity_valid=True,
                                terminal_counts=_terminal_rows(terminal_groups),
                            )
                        expected_latency = EXPECTED_LATENCY[(countdown, clock_k)]
                        if (
                            result["visible_order"] != graph
                            or result["latency"] != expected_latency
                        ):
                            return _stopped(
                                reason=(
                                    "visible event order or event-to-action latency differs "
                                    "from the declared same-tick renewal order"
                                ),
                                counts=counts, population_established=True,
                                integrity_valid=False,
                                terminal_counts=_terminal_rows(terminal_groups),
                            )
                        endpoints.append({
                            "base_state": state["base_state"],
                            "countdown": countdown,
                            "clock": clock_k,
                            "graph": graph,
                            "tape_index": tape_index,
                            "Y": int(result["Y"]),
                            "event_tick": int(result["event_tick"]),
                            "event_to_first_matched_action_latency": int(result["latency"]),
                            **{field: int(result[field]) for field in COUNT_FIELDS},
                        })
                        if clock() >= deadline:
                            return _stopped(
                                reason="1,800 second cap crossed at a candidate-mission boundary",
                                counts=counts, population_established=True,
                                integrity_valid=False,
                                terminal_counts=_terminal_rows(terminal_groups),
                            )

    ys = {
        (row["base_state"], row["countdown"], row["clock"], row["graph"], row["tape_index"]):
        int(row["Y"])
        for row in endpoints
    }
    kbd_rows: list[dict[str, object]] = []
    for state in states:
        base = str(state["base_state"])
        for countdown in COUNTDOWNS:
            value = sum(
                ys[(base, countdown, 7, graph, tape_index)]
                - ys[(base, countdown, 13, graph, tape_index)]
                for graph in GRAPHS for tape_index in range(16)
            )
            kbd_rows.append({"base_state": base, "countdown": countdown, "K_b_d": value})
    kd = {
        countdown: sum(
            int(row["K_b_d"]) for row in kbd_rows if row["countdown"] == countdown
        )
        for countdown in COUNTDOWNS
    }
    values7 = [int(row["K_b_d"]) for row in kbd_rows if row["countdown"] == 7]
    values78 = [int(row["K_b_d"]) for row in kbd_rows if row["countdown"] == 78]
    n = {
        "N_7_plus": sum(value >= 32 for value in values7),
        "N_7_minus": sum(value <= -32 for value in values7),
        "N_78_minus": sum(value <= -32 for value in values78),
        "N_78_plus": sum(value >= 32 for value in values78),
    }
    short = kd[7] >= 192 and n["N_7_plus"] >= 4 and n["N_7_minus"] <= 1
    long = kd[78] <= -192 and n["N_78_minus"] >= 4 and n["N_78_plus"] <= 1
    all_zero = all(int(row["K_b_d"]) == 0 for row in kbd_rows)
    terminal_rows = _terminal_rows(terminal_groups)
    means = []
    for key in terminal_groups:
        base, countdown, clock_k, graph = key
        total_y = sum(
            int(row["Y"]) for row in endpoints
            if (row["base_state"], row["countdown"], row["clock"], row["graph"]) == key
        )
        means.append({
            "base_state": base, "countdown": countdown, "clock": clock_k,
            "graph": graph, "mean_utility": total_y / (16 * HORIZON),
        })
    counts["native_transitions"] = counts["source_transitions"] + counts["candidate_transitions"]
    counts["native_missions"] = counts["source_trajectories"] + counts["candidate_missions"]
    integrity_valid = (
        len(states) == 6
        and [
            (state["source_domain"], state["source_k"], state["tick"])
            for state in states
        ] == [
            (domain, source_k, tick)
            for domain, source_k in SOURCE_DOMAINS for tick in SOURCE_TICKS
        ]
        and len(tapes) == 96
        and len(endpoints) == 768
        and len(ys) == 768
        and counts["source_trajectories"] == 2
        and counts["source_transitions"] > 0
        and counts["candidate_missions"] == 768
        and counts["native_missions"] == 770
        and counts["candidate_transitions"] > 0
        and counts["evaluator_calls"] == 768
        and counts["native_transitions"] > 0
        and sum(
            int(row["safe_dock"]) + int(row["timeout"]) + int(row["failure"])
            for row in endpoints
        ) == 768
    )
    return {
        "branch": _rule(
            integrity_valid=integrity_valid, population_established=True,
            k7=kd[7], k78=kd[78],
            n7_plus=n["N_7_plus"], n7_minus=n["N_7_minus"],
            n78_minus=n["N_78_minus"], n78_plus=n["N_78_plus"],
            all_zero=all_zero,
        ),
        "integrity_valid": integrity_valid,
        "population_established": True,
        "base_states": [
            {
                "base_state": state["base_state"], "source_domain": state["source_domain"],
                "source_k": state["source_k"], "tick": state["tick"],
                "public_observation": state["public_observation"],
            }
            for state in states
        ],
        "scenario_public_inputs": [
            {
                "base_state": state["base_state"], "public_observation": state["public_observation"],
                "time_to_event": countdown,
            }
            for state in states for countdown in COUNTDOWNS
        ],
        "endpoints": endpoints,
        "K_b_d": kbd_rows,
        "K_d": {"7": kd[7], "78": kd[78]},
        **n,
        "SHORT_ALIGNMENT": short,
        "LONG_ALIGNMENT": long,
        "terminal_counts": terminal_rows,
        "mean_utility": means,
        "counts": counts,
        "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
    }


def run_technical_smoke(build_root: Path) -> dict[str, object]:
    """Exercise aligned/intrahold calendar order using toy-only domains."""

    started = time.perf_counter()
    with Host(build_root) as host:
        states, source = host.source_population(
            seed=17,
            domains=(("SCDMP-D6-A02/TOY/SOURCE", 7),),
            targets=(7,),
        )
        tape = materialize_tape(29, "SCDMP-D6-A02/TOY/EVALUATION", ("toy", 0))
        mission_started = time.perf_counter()
        aligned = host.mission(
            states[0], countdown=7, clock_k=7, graph="HR", tape=tape,
        )
        intrahold = host.mission(
            states[0], countdown=7, clock_k=13, graph="RH", tape=tape,
        )
        mission_seconds = time.perf_counter() - mission_started
    results = (aligned, intrahold)
    t_native_mission = mission_seconds / len(results)
    return {
        "mode": "technical-smoke",
        "scientific_state_created": False,
        "event_schedule": [
            {
                "kind": "aligned", "clock": 7, "graph": "HR",
                "event_applied": aligned["event_applied"],
                "visible_order": aligned["visible_order"], "latency": aligned["latency"],
            },
            {
                "kind": "intrahold", "clock": 13, "graph": "RH",
                "event_applied": intrahold["event_applied"],
                "visible_order": intrahold["visible_order"], "latency": intrahold["latency"],
            },
        ],
        "counts": {
            "source_trajectories": source["source_trajectories"],
            "native_missions": len(results),
            "native_transitions": int(source["source_transitions"])
            + sum(int(row["transitions"]) for row in results),
        },
        "unit_seconds": {"native_mission": t_native_mission},
        "projected_counts": {"native_missions": 770},
        "projected_seconds": 2 * (t_native_mission * 770) + 60.0,
        "cap_seconds": 1800.0,
        "wall_seconds": time.perf_counter() - started,
    }


__all__ = ["run_census", "run_technical_smoke"]
