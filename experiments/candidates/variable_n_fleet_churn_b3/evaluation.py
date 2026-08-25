from __future__ import annotations

import statistics
import struct
import sys
import time
from dataclasses import replace

import numpy as np
import torch

from .allocator import frozen_bids, handoff_bids, sp_rda, zero_bids
from .config import CHURNS, EVAL_SCHEDULES, EXECUTABLE_ARMS, GEOMETRIES, MASSES, REGISTERED
from .generator import SeedBanks, World, conclusion_row_order
from .host import evaluate_physical
from .models import SetBidActorCritic
from .rng import opaque_handle


def _deep_words(*objects: object) -> int:
    seen: set[int] = set(); word = struct.calcsize("P")
    def size(value: object) -> int:
        identity = id(value)
        if identity in seen:
            return 0
        seen.add(identity)
        total = sys.getsizeof(value)
        if isinstance(value, np.ndarray):
            total += int(value.nbytes)
        elif isinstance(value, dict):
            total += sum(size(k) + size(v) for k, v in value.items())
        elif isinstance(value, (list, tuple, set, frozenset)):
            total += sum(size(item) for item in value)
        return total
    return (sum(size(item) for item in objects) + word - 1) // word


def _permute_bid_association(world: World, handles: list[str], bids: np.ndarray) -> np.ndarray:
    result = bids.copy()
    for members in (
        [i for i, h in enumerate(handles) if h in world.previous_roles],
        [i for i, h in enumerate(handles) if h not in world.previous_roles],
    ):
        if len(members) < 2:
            continue
        ordered = sorted(members, key=lambda row: world.tie_ranks[handles[row]])
        for position, target in enumerate(ordered):
            result[target] = bids[ordered[(position + 1) % len(ordered)]]
    return result


def _learned_bids(model: SetBidActorCritic, agents: np.ndarray, tasks: np.ndarray, global_row: np.ndarray):
    with torch.no_grad():
        output = model(
            torch.from_numpy(agents), torch.from_numpy(tasks), torch.from_numpy(global_row),
            lease_vector=torch.zeros(len(agents), dtype=torch.float32),
        )
        bids = model.deterministic_bids(output).numpy()
    return bids, model.learned_forward_counts(len(agents)), output.peak_n_dependent_tensor_words


def execute_arm(
    model: SetBidActorCritic, world: World, arm: str, order: list[int], *,
    measure_outcome: bool = True, record_timing: bool = True,
) -> tuple[dict, dict, int, int, dict]:
    start_full = time.perf_counter_ns() if record_timing else 0
    handles, agents, tasks, global_row = world.observation(order)
    capacities = world.capacities[order]
    learned_counts = {"task_agent_attention_scores": 0, "bid_latents": 0,
                      "agent_agent_scores": 0, "nxn_tensors": 0}
    model_words = 0; bid_phase_words = 0
    if arm == "ZERO-RDA":
        bids = zero_bids(capacities, world.demand); bid_phase_words = _deep_words(bids)
    elif arm == "FROZEN-RDA":
        bids = frozen_bids(capacities, world.demand); bid_phase_words = 2 * _deep_words(bids)
    elif arm == "HANDOFF-RDA":
        bids = handoff_bids(handles, capacities, world.demand, world.previous_roles, world.new_handles)
        bid_phase_words = 3 * _deep_words(bids)
    elif arm in ("G-RELEASE", "G-PERMUTE"):
        bids, learned_counts, model_words = _learned_bids(model, agents, tasks, global_row)
        if arm == "G-PERMUTE":
            bids = _permute_bid_association(world, handles, bids)
    else:
        raise ValueError(f"non-Stage-1 arm rejected: {arm}")
    allocator_start = time.perf_counter_ns() if record_timing else 0
    assignment, counters = sp_rda(
        handles, capacities, world.demand, bids, world.tie_ranks,
        learned_nxn_object=bool(learned_counts.get("nxn_tensors", 0)),
    )
    base_words = _deep_words(
        world.handles, world.capacities, world.previous_roles, world.new_handles,
        world.tie_ranks, handles, agents, capacities,
    )
    allocator_phase_words = _deep_words(bids, assignment) + int(counters["peak_live_edge_machine_words"])
    m_dep = int(base_words + max(model_words, bid_phase_words, allocator_phase_words))
    counters["memory"] = {
        "machine_word_bytes": struct.calcsize("P"), "base_n_dependent_words": base_words,
        "model_peak_n_dependent_words": model_words, "bid_phase_n_dependent_words": bid_phase_words,
        "allocator_phase_n_dependent_words": allocator_phase_words, "M_dep_words": m_dep,
        "M_dep_le_1024N": m_dep <= 1024 * world.n,
    }
    allocator_ns = time.perf_counter_ns() - allocator_start if record_timing else 0
    full_ns = time.perf_counter_ns() - start_full if record_timing else 0
    outcome = (evaluate_physical(handles, capacities, world.demand, world.previous_roles, assignment).as_dict()
               if measure_outcome else {"assignment": assignment})
    return outcome, counters, full_ns, allocator_ns, learned_counts


def evaluate_seed(seed: int, model: SetBidActorCritic, banks: SeedBanks) -> tuple[list[dict], dict]:
    rows: list[dict] = []; complexity_failures: list[dict] = []; invariance_failures: list[dict] = []
    opportunity: dict[str, int] = {}; operation_totals = {
        arm: {name: 0 for name in ("events", "edges", "edge_key_evaluations", "heap_build_records",
                                   "heap_builds", "heap_pops", "heap_key_comparisons", "residual_updates",
                                   "task_agent_attention_scores", "bid_latents", "agent_agent_scores")}
        for arm in EXECUTABLE_ARMS
    }
    zero_equality_checks = tagged_ceilings = 0
    for schedule_index, schedule in enumerate(EVAL_SCHEDULES):
        for panel in banks.conclusion[schedule_index]:
            for mass in MASSES:
                for geometry in GEOMETRIES:
                    for churn in CHURNS:
                        world = panel.worlds[(mass, geometry, churn)]
                        tagged_ceilings += 1
                        ceiling = float(world.certificates["unrestricted_ceiling"])
                        replicas: dict[str, list[dict]] = {arm: [] for arm in EXECUTABLE_ARMS}
                        mapped: dict[str, dict[int, dict[str, int]]] = {arm: {} for arm in EXECUTABLE_ARMS}
                        for replica in range(4):
                            order = conclusion_row_order(world, replica)
                            for arm in EXECUTABLE_ARMS:
                                outcome, counters, full_ns, allocator_ns, learned = execute_arm(model, world, arm, order)
                                replicas[arm].append({"outcome": outcome, "counters": counters,
                                                      "full_ns": full_ns, "allocator_ns": allocator_ns,
                                                      "learned": learned})
                                mapped[arm][replica] = outcome["assignment"]
                                totals = operation_totals[arm]; totals["events"] += 1
                                for name in ("edges", "edge_key_evaluations", "heap_build_records", "heap_builds",
                                             "heap_pops", "heap_key_comparisons", "residual_updates"):
                                    totals[name] += int(counters[name])
                                for name in ("task_agent_attention_scores", "bid_latents", "agent_agent_scores"):
                                    totals[name] += int(learned.get(name, 0))
                                failed = [name for name, ok in counters["guards"].items() if not ok]
                                if not counters["memory"]["M_dep_le_1024N"]:
                                    failed.append("M_dep_le_1024N")
                                if failed:
                                    complexity_failures.append({"raw_index": world.raw_index, "arm": arm,
                                                                "replica": replica, "failed": failed})
                            handles, _, _, _ = world.observation(order); caps = world.capacities[order]
                            zeroed, _ = sp_rda(handles, caps, world.demand, np.zeros((world.n, 3)), world.tie_ranks)
                            if zeroed != replicas["ZERO-RDA"][-1]["outcome"]["assignment"]:
                                raise RuntimeError("zeroed learned-bid diagnostic differs from ZERO-RDA")
                            zero_equality_checks += 1
                        invariant: dict[str, bool] = {}
                        for arm in EXECUTABLE_ARMS:
                            invariant[arm] = all(mapped[arm][r] == mapped[arm][0] for r in range(1, 4))
                            if not invariant[arm]:
                                invariance_failures.append({"raw_index": world.raw_index, "schedule_index": schedule_index,
                                                            "mass": mass, "geometry": geometry, "churn": churn, "arm": arm})
                        fixed_assignments = [mapped[a][0] for a in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA")]
                        at_least_two = any(fixed_assignments[i] != fixed_assignments[j]
                                           for i in range(3) for j in range(i + 1, 3))
                        fixed_returns = [replicas[a][0]["outcome"]["J"]
                                         for a in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA")]
                        contested = bool(at_least_two and any(ceiling - value >= .05 - 1e-12 for value in fixed_returns))
                        if world.n == 15 and geometry == "COUPLED" and contested:
                            key = f"{schedule[0]}->{schedule[1]}|{mass}|{churn}"
                            opportunity[key] = opportunity.get(key, 0) + 1
                        for arm in EXECUTABLE_ARMS:
                            reps = replicas[arm]
                            row = {
                                "seed": seed, "schedule_index": schedule_index, "raw_index": world.raw_index,
                                "retained_index": world.retained_index, "schedule": f"{schedule[0]}->{schedule[1]}",
                                "pre_n": schedule[0], "n": schedule[1], "mass": mass, "geometry": geometry,
                                "churn": churn, "arm": arm, "ceiling_J": ceiling, "contested": contested,
                                "assignment": mapped[arm][0], "row_order_assignment_invariant": invariant[arm],
                                "service": np.mean([x["outcome"]["service"] for x in reps], axis=0).tolist(),
                                "waste": np.mean([x["outcome"]["waste"] for x in reps], axis=0).tolist(),
                                "full_decision_ns": [x["full_ns"] for x in reps],
                                "allocator_ns": [x["allocator_ns"] for x in reps],
                                "counters": reps[0]["counters"], "learned_counts": reps[0]["learned"],
                            }
                            for metric in ("J", "Trec", "survivor_switch_fraction", "dummy_fraction"):
                                row[metric] = float(np.mean([x["outcome"][metric] for x in reps]))
                            row["GAP"] = ceiling - float(row["J"])
                            for other in ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA", "G-PERMUTE"):
                                row[f"disagree_G_{other}"] = (mapped["G-RELEASE"][0] != mapped[other][0]
                                                                    if invariant["G-RELEASE"] and invariant[other] else None)
                            rows.append(row)
    if tagged_ceilings != 768 or len(rows) != 768 * 5:
        raise RuntimeError(f"evaluation count mismatch ceilings={tagged_ceilings} rows={len(rows)}")
    latency = []
    for n in (12, 15):
        for arm in EXECUTABLE_ARMS:
            selected = [r for r in rows if r["n"] == n and r["arm"] == arm]
            full_ms = [value / 1e6 for r in selected for value in r["full_decision_ns"]]
            allocator_ms = [value / 1e6 for r in selected for value in r["allocator_ns"]]
            latency.append({"n": n, "arm": arm, "count": len(full_ms),
                            "full_p50_ms": float(np.percentile(full_ms, 50)),
                            "full_p95_ms": float(np.percentile(full_ms, 95)),
                            "allocator_p50_ms": float(np.percentile(allocator_ms, 50)),
                            "allocator_p95_ms": float(np.percentile(allocator_ms, 95))})
    return rows, {
        "seed": seed, "base_worlds": 768, "tagged_certificate_ceilings": tagged_ceilings,
        "row_replicas_per_executable_arm": 3072, "executable_evaluations": 15360,
        "zero_bid_equality_checks": zero_equality_checks, "primary_contested_opportunities": opportunity,
        "complexity_failures": complexity_failures, "row_order_invariance_failures": invariance_failures,
        "operation_totals": operation_totals, "evaluation_event_decision_latency": latency,
    }


def audit_source(banks: SeedBanks) -> World:
    panel = banks.conclusion[2][0]
    return panel.worlds[("FIXED_MASS", "COUPLED", "SWITCH_REQUIRED")]


def _clone_world(source: World, q: int) -> World:
    handles: list[str] = []; capacities: list[np.ndarray] = []; previous: dict[str, int] = {}; new: set[str] = set()
    for source_row, source_handle in enumerate(source.handles):
        for clone in range(q):
            handle = opaque_handle(1601, "complexity-audit-clone", q, source_row, clone)
            handles.append(handle); capacities.append(source.capacities[source_row] / q)
            if source_handle in source.previous_roles: previous[handle] = int(source.previous_roles[source_handle])
            if source_handle in source.new_handles: new.add(handle)
    handle_tuple = tuple(handles)
    world = replace(
        source, split="complexity-audit", schedule_index=2, raw_index=source.raw_index,
        schedule=(12 * q, 15 * q), handles=handle_tuple, capacities=np.asarray(capacities),
        previous_roles=previous, new_handles=frozenset(new), tie_ranks={h: rank for rank, h in enumerate(handle_tuple)},
    )
    if not np.allclose(world.capacities.sum(0), source.capacities.sum(0), rtol=1e-12, atol=1e-12):
        raise RuntimeError("audit clone failed exact task-mass preservation")
    return world


def complexity_audit(model: SetBidActorCritic, source: World, environment: dict) -> dict:
    records: list[dict] = []
    for q in (1, 2, 4, 8):
        world = _clone_world(source, q); n = world.n; order = list(range(n))
        for arm in EXECUTABLE_ARMS:
            for _ in range(REGISTERED.audit_warmups):
                execute_arm(model, world, arm, order, measure_outcome=False, record_timing=False)
            full: list[float] = []; allocator: list[float] = []; mdep: list[int] = []; guards: list[bool] = []
            operation = {name: [] for name in ("edges", "edge_key_evaluations", "heap_build_records",
                                                "heap_builds", "heap_pops", "heap_key_comparisons",
                                                "residual_updates", "peak_live_edge_records")}
            for _ in range(REGISTERED.audit_repeats):
                _, counters, full_ns, allocator_ns, _ = execute_arm(model, world, arm, order, measure_outcome=False)
                full.append(full_ns / 1e6); allocator.append(allocator_ns / 1e6)
                mdep.append(int(counters["memory"]["M_dep_words"]))
                guards.append(all(counters["guards"].values()) and counters["memory"]["M_dep_le_1024N"])
                for name in operation: operation[name].append(int(counters[name]))
            sorted_full = sorted(full); sorted_allocator = sorted(allocator)
            records.append({
                "checkpoint_seed": 1601, "source_seed": 1601, "source_retained_index": 0,
                "source_raw_index": source.raw_index, "source_schedule": "12->15",
                "source_mass": "FIXED_MASS", "source_geometry": "COUPLED",
                "source_churn": "SWITCH_REQUIRED", "q": q, "n": n, "arm": arm,
                "warmups": REGISTERED.audit_warmups, "repeats": REGISTERED.audit_repeats,
                "full_p50_ms": float(statistics.median(full)), "full_p95_ms": float(sorted_full[243]),
                "allocator_p50_ms": float(statistics.median(allocator)),
                "allocator_p95_ms": float(sorted_allocator[243]),
                "M_dep_words": {"min": min(mdep), "median": float(statistics.median(mdep)), "max": max(mdep)},
                "median_M_dep_words_per_agent": float(statistics.median(mdep) / n),
                "every_repeat_M_dep_le_1024N": all(value <= 1024 * n for value in mdep),
                "operation_counters_per_call": {name: {"min": min(v), "median": float(statistics.median(v)), "max": max(v)}
                                                  for name, v in operation.items()},
                "all_operation_and_memory_guards": all(guards),
            })
    gates: list[dict] = []
    for arm in EXECUTABLE_ARMS:
        selected = {r["n"]: r for r in records if r["arm"] == arm}
        base = selected[15]["median_M_dep_words_per_agent"]
        ratios = {f"{n}->{2*n}": selected[2*n]["full_p95_ms"] / max(selected[n]["full_p95_ms"], 1e-12)
                  for n in (15, 30, 60)}
        gates.append({
            "arm": arm, "n15_p95_le_25ms": selected[15]["full_p95_ms"] <= 25.0,
            "n120_p95_le_100ms": selected[120]["full_p95_ms"] <= 100.0,
            "doubling_ratios": ratios, "doubling_ratios_le_2p75": all(v <= 2.75 for v in ratios.values()),
            "every_repeat_M_dep_le_1024N": all(selected[n]["every_repeat_M_dep_le_1024N"] for n in (15,30,60,120)),
            "median_per_agent_memory_scaling": all(selected[n]["median_M_dep_words_per_agent"] <= 2 * base
                                                    for n in (15,30,60,120)),
            "operation_guards": all(selected[n]["all_operation_and_memory_guards"] for n in (15,30,60,120)),
        })
    return {
        "environment": environment, "source": {"seed": 1601, "schedule_index": 2,
            "retained_index": 0, "raw_index": source.raw_index, "mass": source.mass,
            "geometry": source.geometry, "churn": source.churn},
        "warmup_repeats": 64, "timed_repeats": 256, "p95_order_statistic": 244,
        "records": records, "gates": gates,
        "all_gates_except_process_rss": all(
            gate["n15_p95_le_25ms"] and gate["n120_p95_le_100ms"] and gate["doubling_ratios_le_2p75"]
            and gate["every_repeat_M_dep_le_1024N"] and gate["median_per_agent_memory_scaling"]
            and gate["operation_guards"] for gate in gates),
    }
