"""A01 source-population construction, native census and exact integer rule inputs."""

from __future__ import annotations

from pathlib import Path
import time

from .native import ACTIONS, EVALUATION_DOMAIN, GRAPHS, HORIZON, Host
from .rng import disturbance_tape
from .rule import decide_branch


COUNT_FIELDS = (
    "safe_dock",
    "timeout",
    "failure",
    "cable_overload",
    "gantry_contact",
    "attitude_loss",
    "formation_loss",
)


def _invalid_census(
    reason: str,
    counts: dict[str, object],
    terminal_rows: list[dict[str, object]],
    *,
    source_population_established: bool,
) -> dict[str, object]:
    counts["native_transitions"] = (
        counts["source_transitions"] + counts["candidate_transitions"]
    )
    return {
        "branch": decide_branch(
            resource_ready=True,
            integrity_valid=False,
            source_population_established=source_population_established,
            w=0,
            r7=0,
            r13=0,
        ),
        "integrity_valid": False,
        "source_population_established": source_population_established,
        "reason": reason,
        "counts": counts,
        "terminal_counts": terminal_rows,
        "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
    }


def run_census(host: Host, *, deadline: float, clock=time.perf_counter) -> dict[str, object]:
    states, source = host.source_population(deadline=deadline, clock=clock)
    counts = {
        "source_trajectories": source["source_trajectories"],
        "source_renewals": source["source_renewals"],
        "source_transitions": source["source_transitions"],
        "candidate_missions": 0,
        "candidate_transitions": 0,
        "evaluator_calls": 0,
        "models": 0,
        "training_datasets": 0,
        "optimizer_updates": 0,
        "adamw_steps": 0,
        "learner_evaluations": 0,
    }
    if source["cap_crossed"]:
        return _invalid_census(
            str(source["reason"]), counts, [], source_population_established=False,
        )
    if not source["established"]:
        return {
            "branch": decide_branch(
                resource_ready=True,
                integrity_valid=True,
                source_population_established=False,
                w=0,
                r7=0,
                r13=0,
            ),
            "source_population_established": False,
            "source_population_reason": source["reason"],
            "counts": counts,
            "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
        }

    # All 6 x 16 future tapes exist before the first candidate endpoint is read.
    tapes = host.materialize_evaluation_tapes(states, seed=EVALUATION_DOMAIN)
    sums = [[0 for _ in ACTIONS] for _ in states]
    terminal_rows: list[dict[str, object]] = []
    for state_index, state in enumerate(states):
        for action_index, action in enumerate(ACTIONS):
            for graph in GRAPHS:
                terminal = {field: 0 for field in COUNT_FIELDS}
                for tape_index in range(16):
                    result = host.mission(
                        state,
                        graph,
                        action,
                        tapes[(state_index, tape_index)],
                    )
                    sums[state_index][action_index] += int(result["Y"])
                    counts["candidate_missions"] += 1
                    counts["evaluator_calls"] += 1
                    counts["candidate_transitions"] += int(result["transitions"])
                    for field in COUNT_FIELDS:
                        terminal[field] += int(result[field])
                    if clock() >= deadline:
                        terminal_rows.append({
                            "state_id": state["state_id"],
                            "action": list(action),
                            "graph": graph,
                            "missions": tape_index + 1,
                            "complete": False,
                            **terminal,
                        })
                        return _invalid_census(
                            "1,800 second cap crossed at a candidate-mission boundary",
                            counts,
                            terminal_rows,
                            source_population_established=True,
                        )
                terminal_rows.append({
                    "state_id": state["state_id"],
                    "action": list(action),
                    "graph": graph,
                    "missions": 16,
                    "complete": True,
                    **terminal,
                })

    value_rows: list[dict[str, object]] = []
    duration_rows: list[dict[str, object]] = []
    w_rows: list[dict[str, object]] = []
    for state, state_sums in zip(states, sums, strict=True):
        for action, total in zip(ACTIONS, state_sums, strict=True):
            value_rows.append({
                "state_id": state["state_id"],
                "action": list(action),
                "S": total,
                "V": total / (32 * HORIZON),
            })
        b7 = max(state_sums[index] for index, action in enumerate(ACTIONS) if action[1] == 7)
        b13 = max(state_sums[index] for index, action in enumerate(ACTIONS) if action[1] == 13)
        difference = b7 - b13
        span = max(state_sums) - min(state_sums)
        duration_rows.append({
            "state_id": state["state_id"],
            "B7": b7,
            "B13": b13,
            "D": difference,
        })
        w_rows.append({"state_id": state["state_id"], "W_j": span})

    r7 = int(any(row["D"] >= 32 for row in duration_rows))
    r13 = int(any(row["D"] <= -32 for row in duration_rows))
    w = sum(row["W_j"] for row in w_rows)
    counts["native_transitions"] = counts["source_transitions"] + counts["candidate_transitions"]
    integrity_valid = (
        len(states) == 6
        and counts["candidate_missions"] == 1152
        and counts["evaluator_calls"] == 1152
        and counts["native_transitions"] > 0
        and sum(row["safe_dock"] + row["timeout"] + row["failure"]
                for row in terminal_rows) == 1152
    )
    return {
        "branch": decide_branch(
            resource_ready=True,
            integrity_valid=integrity_valid,
            source_population_established=True,
            w=w,
            r7=r7,
            r13=r13,
        ),
        "source_population_established": True,
        "states": [{
            "state_id": state["state_id"],
            "source_seed": state["source_seed"],
            "source_k": state["source_k"],
            "target_tick": state["target_tick"],
            "boundary_tick": state["boundary_tick"],
        } for state in states],
        "state_action_values": value_rows,
        "duration_preferences": duration_rows,
        "action_spans": w_rows,
        "R7": r7,
        "R13": r13,
        "W": w,
        "terminal_counts": terminal_rows,
        "counts": counts,
        "integrity_valid": integrity_valid,
        "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
    }


def run_technical_smoke(build_root: Path) -> dict[str, object]:
    """Compile and exercise toy source/twins/candidates without an A coordinate."""

    started = time.perf_counter()
    with Host(build_root) as host:
        states, source = host.source_population(
            streams=((17, 7),),
            targets=(7,),
        )
        tape = disturbance_tape(29, "technical-smoke-disturbance", (0,), holds=64)
        mission_started = time.perf_counter()
        results = [
            host.mission(states[0], graph, (0, 7), tape)
            for graph in GRAPHS
        ]
        mission_seconds = time.perf_counter() - mission_started
    t_native_mission = mission_seconds / len(results)
    return {
        "mode": "technical-smoke",
        "scientific_state_created": False,
        "counts": {
            "source_trajectories": source["source_trajectories"],
            "native_missions": len(results),
            "native_transitions": source["source_transitions"]
            + sum(int(row["transitions"]) for row in results),
        },
        "unit_seconds": {
            "native_mission": t_native_mission,
            "adamw_step": 0.0,
            "candidate_score": 0.0,
        },
        "projected_counts": {
            "native_missions": 1154,
            "adamw_steps": 0,
            "candidate_scores": 0,
        },
        "projected_seconds": 2 * (t_native_mission * 1154) + 60.0,
        "cap_seconds": 1800.0,
        "wall_seconds": time.perf_counter() - started,
    }


__all__ = ["run_census", "run_technical_smoke"]
