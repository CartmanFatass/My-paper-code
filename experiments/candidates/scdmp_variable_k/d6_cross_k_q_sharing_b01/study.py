"""Gate, common data, learner arms, and frozen estimands."""

from __future__ import annotations

import math
import statistics
import time

import torch

from .model import ValueModel, displacement, optimizer
from .native import ACTIONS, EVALUATION_DOMAIN, GRAPHS, Host, TARGET_TICKS
from .rules import decide_branch


LEARNER_SEEDS = (3119, 5171, 8089)
CHECKPOINTS = (0, 20, 40, 60, 80, 100, 120, 140, 160)


def _timed(bucket: dict[str, float], key: str, function):
    started = time.perf_counter()
    value = function()
    now = time.perf_counter()
    bucket[key] = bucket.get(key, 0.0) + now - started
    if "_deadline" in bucket and now > bucket["_deadline"]:
        raise TimeoutError("1,800 second invocation cap exceeded")
    return value


def _evaluation_mission(
    host: Host, state: dict[str, object], graph: str, action: tuple[int, int], tape_index: int,
) -> tuple[float, int]:
    tape = host.evaluation_tape(str(state["state_id"]), tape_index)
    return host.mission(state, graph, action, tape)


def _training_mission(
    host: Host, state: dict[str, object], graph: str, action_index: int,
    seed: int, update: int, record_index: int,
) -> tuple[float, int]:
    tape = host.training_tape(
        seed, update, record_index, str(state["state_id"]), graph, action_index,
    )
    return host.mission(state, graph, ACTIONS[action_index], tape)


def run_gate(
    host: Host, *, tapes: int = 16, targets: tuple[int, ...] = TARGET_TICKS,
    timing: dict[str, float] | None = None,
) -> dict[str, object]:
    timing = {} if timing is None else timing
    states, source_transitions = host.source_states(targets)
    cells = []
    transitions = 0
    for state in states:
        for action_index, action in enumerate(ACTIONS):
            for graph in GRAPHS:
                for tape_index in range(tapes):
                    utility, count = _timed(
                        timing, "native_seconds",
                        lambda s=state, g=graph, a=action, t=tape_index:
                            _evaluation_mission(host, s, g, a, t),
                    )
                    transitions += count
                    cells.append({
                        "state_id": state["state_id"], "action_index": action_index,
                        "graph": graph, "tape": tape_index, "utility": utility,
                        "transitions": count,
                    })
    oracle = {}
    denominator = 0.0
    for state in states:
        state_id = str(state["state_id"])
        values = []
        for action_index in range(len(ACTIONS)):
            rows = [
                float(row["utility"]) for row in cells
                if row["state_id"] == state_id and row["action_index"] == action_index
            ]
            values.append(math.fsum(rows) / len(rows))
        best, worst = max(values), min(values)
        first = values.index(best)
        best_k = ACTIONS[first][1]
        other_best = max(value for value, action in zip(values, ACTIONS, strict=True) if action[1] != best_k)
        optimal_durations = sorted({
            action[1] for value, action in zip(values, ACTIONS, strict=True) if value == best
        })
        margin = best - other_best
        oracle[state_id] = {
            "values": values, "best": best, "worst": worst,
            "first_best_action_index": first, "first_best_k": best_k,
            "optimal_durations": optimal_durations, "cross_duration_margin": margin,
        }
        denominator += best - worst
    tick = 1.0 / 364.0
    has_7 = any(row["first_best_k"] == 7 and row["cross_duration_margin"] >= tick for row in oracle.values())
    has_13 = any(row["first_best_k"] == 13 and row["cross_duration_margin"] >= tick for row in oracle.values())
    return {
        "states": states, "oracle": oracle, "cells": cells,
        "evaluation_domain": EVALUATION_DOMAIN, "evaluation_tapes_per_state": tapes,
        "native_missions": len(cells), "native_transitions": transitions,
        "source_transitions": source_transitions, "regret_denominator": denominator,
        "duration_7_distinct": has_7, "duration_13_distinct": has_13,
        "positive_oracle_span": denominator > 0.0,
        "host_pass": has_7 and has_13 and denominator > 0.0,
    }


def generate_dataset(
    host: Host, gate: dict[str, object], seed: int, *, updates: int = 160,
    timing: dict[str, float] | None = None,
) -> dict[str, object]:
    timing = {} if timing is None else timing
    states = gate["states"]
    records = []
    transitions = 0
    for update in range(updates):
        for record_index in range(12):
            action_index = record_index % 6
            state = states[(action_index + update) % len(states)]
            graph = GRAPHS[record_index // 6]
            utility, count = _timed(
                timing, "native_seconds",
                lambda s=state, g=graph, a=action_index, u=update, r=record_index:
                    _training_mission(host, s, g, a, seed, u, r),
            )
            transitions += count
            records.append({
                "update": update + 1, "order": record_index,
                "state_id": state["state_id"], "graph": graph,
                "observation": state["observation"], "action_index": action_index,
                "z": ACTIONS[action_index][0], "k": ACTIONS[action_index][1],
                "target": utility, "transitions": count,
            })
    return {
        "learner_seed": seed, "updates": updates, "records": records,
        "native_missions": len(records), "native_transitions": transitions,
        "training_rng_domain": "training-disturbance",
    }


def _evaluate(
    host: Host, model: ValueModel, gate: dict[str, object], update: int, tapes: int,
    timing: dict[str, float],
) -> dict[str, object]:
    selections = []
    regret_numerator = 0.0
    optimal_duration_count = 0
    native_missions = 0
    native_transitions = 0
    candidate_scores = 0
    for state in gate["states"]:
        scores = _timed(
            timing, "candidate_score_seconds",
            lambda s=state: [model.score(s["observation"], z, k) for z, k in ACTIONS],
        )
        candidate_scores += len(scores)
        selected = max(range(len(scores)), key=scores.__getitem__)
        values = []
        for graph in GRAPHS:
            for tape_index in range(tapes):
                utility, count = _timed(
                    timing, "native_seconds",
                    lambda s=state, g=graph, a=ACTIONS[selected], t=tape_index:
                        _evaluation_mission(host, s, g, a, t),
                )
                values.append(utility)
                native_missions += 1
                native_transitions += count
        native_value = math.fsum(values) / len(values)
        oracle = gate["oracle"][str(state["state_id"])]
        regret_numerator += float(oracle["best"]) - native_value
        if ACTIONS[selected][1] in oracle["optimal_durations"]:
            optimal_duration_count += 1
        selections.append({
            "state_id": state["state_id"], "action_index": selected,
            "scores": scores, "native_value": native_value,
        })
    return {
        "update": update, "selections": selections,
        "regret": regret_numerator / max(float(gate["regret_denominator"]), 1e-300),
        "optimal_duration_count": optimal_duration_count,
        "native_missions": native_missions, "native_transitions": native_transitions,
        "candidate_scores": candidate_scores,
    }


def train_arm(
    host: Host, gate: dict[str, object], dataset: dict[str, object], arm: str, *,
    checkpoints: tuple[int, ...] = CHECKPOINTS, tapes: int = 16,
    timing: dict[str, float] | None = None,
) -> dict[str, object]:
    timing = {} if timing is None else timing
    seed = int(dataset["learner_seed"])
    torch.set_num_threads(1)
    model = ValueModel(arm, seed)
    initial_head, initial_encoder = model.initial_snapshots()
    opt = optimizer(model)
    evaluations = []
    exposures = []
    learner_steps = 0
    by_update = {}
    for record in dataset["records"]:
        by_update.setdefault(int(record["update"]), []).append(record)
    for update in range(0, int(dataset["updates"]) + 1):
        if update > 0:
            for record in by_update[update]:
                def step() -> None:
                    observation = torch.tensor(record["observation"], dtype=torch.float32).reshape(1, 18)
                    target = torch.tensor([[record["target"]]], dtype=torch.float32)
                    opt.zero_grad(set_to_none=True)
                    loss = (model(observation, int(record["z"]), int(record["k"])) - target).square().mean()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.8)
                    opt.step()
                _timed(timing, "adamw_seconds", step)
                learner_steps += 1
        if update in checkpoints:
            evaluations.append(_evaluate(host, model, gate, update, tapes, timing))
            exposures.append({
                "update": update,
                "head": displacement(model, initial_head, head=True),
                "common_encoder": displacement(model, initial_encoder, head=False),
            })
    competent_flags = [
        row["regret"] <= 0.10 and row["optimal_duration_count"] >= 5
        for row in evaluations
    ]
    retained = [all(competent_flags[index:]) for index in range(len(competent_flags))]
    retained_updates = [row["update"] for row, keep in zip(evaluations, retained, strict=True) if keep]
    competence_update = retained_updates[0] if retained_updates else 180
    auc = statistics.fmean(row["regret"] for row in evaluations if row["update"] > 0)
    return {
        "arm": arm, "learner_seed": seed, "evaluations": evaluations, "exposures": exposures,
        "learner_steps": learner_steps,
        "native_evaluation_missions": sum(row["native_missions"] for row in evaluations),
        "native_evaluation_transitions": sum(row["native_transitions"] for row in evaluations),
        "candidate_scores": sum(row["candidate_scores"] for row in evaluations),
        "competence_update": competence_update, "competent": competence_update <= checkpoints[-1],
        "auc": auc, "final_native_return": statistics.fmean(
            row["native_value"] for row in evaluations[-1]["selections"]
        ),
        "dataset_native_transitions": dataset["native_transitions"],
        "dataset_records": dataset["records"],
        "training_rng_domain": dataset["training_rng_domain"],
    }


def summarize(gate: dict[str, object], arms: list[dict[str, object]]) -> dict[str, object]:
    pairs = {}
    for row in arms:
        pairs.setdefault(int(row["learner_seed"]), {})[str(row["arm"])] = row
    seed_rows = []
    for seed in LEARNER_SEEDS:
        d6, d8 = pairs[seed]["D6"], pairs[seed]["D8"]
        witness_cells = []
        for left, right in zip(d6["evaluations"], d8["evaluations"], strict=True):
            if left["update"] >= d8["competence_update"]:
                continue
            for d6_choice, d8_choice in zip(left["selections"], right["selections"], strict=True):
                state_id = str(d6_choice["state_id"])
                oracle = gate["oracle"][state_id]
                a6, a8 = int(d6_choice["action_index"]), int(d8_choice["action_index"])
                if (
                    ACTIONS[a6][1] in oracle["optimal_durations"]
                    and ACTIONS[a8][1] != ACTIONS[a6][1]
                    and oracle["values"][a6] - oracle["values"][a8] >= 1.0 / 364.0
                ):
                    witness_cells.append({"update": left["update"], "state_id": state_id})
        seed_rows.append({
            "seed": seed, "d6_competent": d6["competent"], "d8_competent": d8["competent"],
            "delta_t": d8["competence_update"] - d6["competence_update"],
            "delta_auc": d8["auc"] - d6["auc"], "witness": bool(witness_cells),
            "witness_cells": witness_cells,
            "final_return_difference": d6["final_native_return"] - d8["final_native_return"],
        })
    exposure_final = {
        arm: [float(pairs[seed][arm]["exposures"][-1]["head"]["ratio"]) for seed in LEARNER_SEEDS]
        for arm in ("D6", "D8")
    }
    integrity = (
        gate["native_missions"] == 1152 and gate["native_transitions"] > 0
        and gate["source_transitions"] > 0 and gate["evaluation_domain"] == EVALUATION_DOMAIN
        and gate.get("admission", {}).get("passed") is True
        and all(row["learner_steps"] == 1920 for row in arms)
        and all(row["native_evaluation_missions"] == 1728 for row in arms)
        and all(row["native_evaluation_transitions"] > 0 for row in arms)
        and all(row["candidate_scores"] == 324 for row in arms)
        and all(row["dataset_native_transitions"] > 0 for row in arms)
        and all(len(row["dataset_records"]) == 1920 for row in arms)
        and all(
            [entry["update"] for entry in row["evaluations"]] == list(CHECKPOINTS)
            and [entry["update"] for entry in row["exposures"]] == list(CHECKPOINTS)
            for row in arms
        )
        and all(row.get("admission", {}).get("passed") is True for row in arms)
        and all(row.get("data_admission", {}).get("passed") is True for row in arms)
        and all(
            pairs[seed]["D6"]["dataset_records"] == pairs[seed]["D8"]["dataset_records"]
            for seed in LEARNER_SEEDS
        )
        and all(row["training_rng_domain"] == "training-disturbance" for row in arms)
        and all(exp["head"]["valid"] and exp["common_encoder"]["valid"] for row in arms for exp in row["exposures"])
    )
    facts = {
        "integrity_valid": integrity, "host_pass": gate["host_pass"],
        "exposure_final": exposure_final,
        "d6_competent": [row["d6_competent"] for row in seed_rows],
        "d8_competent": [row["d8_competent"] for row in seed_rows],
        "delta_t": [row["delta_t"] for row in seed_rows],
        "delta_auc": [row["delta_auc"] for row in seed_rows],
        "witness": [row["witness"] for row in seed_rows],
        "final_return_difference": [row["final_return_difference"] for row in seed_rows],
    }
    return {"branch": decide_branch(facts), "facts": facts, "seeds": seed_rows}


__all__ = [
    "CHECKPOINTS", "LEARNER_SEEDS", "generate_dataset", "run_gate", "summarize", "train_arm",
]
