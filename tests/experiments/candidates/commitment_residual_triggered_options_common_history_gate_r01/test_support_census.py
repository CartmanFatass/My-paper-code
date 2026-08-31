from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
    support_census as census,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    ACTION_ORDER,
    Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    build_balanced_tapes,
)


def _decision(
    agent: int, *, previous: int, selected: int, charge: float, age_before: int,
    kind: str,
) -> dict[str, object]:
    changed = selected != previous
    return {
        "agent": agent,
        "kind": kind,
        "previous_option": previous,
        "selected_option": selected,
        "changed": changed,
        "charge": charge,
        "age_before": age_before,
        "age_after_decision": 0 if changed else age_before,
        "switch_time": False,
        "reanchored": changed,
    }


def _branch(
    *, printed_index: int, boundary_time: int, cost: float, denominator: int,
    target_g16: float, tape: object,
) -> dict[str, object]:
    selected = 6 if printed_index == 0 else printed_index - 1
    charge = 0.0 if printed_index == 0 else 0.05 + cost
    steps = []
    queues = [0, 0]
    buffers = [32, 32]
    selected_options = [selected, 6, 6, 6]
    ages_after = [0 if selected != 6 else 8, 8, 8, 8]
    for offset in range(16):
        event_active, arrivals, relay_capacity = census._expected_exogenous_step(
            tape, boundary_time + offset,
        )
        step_charge = charge if offset == 0 else 0.0
        step_delivered = [
            min(buffers[lane], relay_capacity[lane]) for lane in range(2)
        ]
        step_energy = 0.0
        queues_after = [queues[lane] + arrivals[lane] for lane in range(2)]
        buffers_after = [buffers[lane] - step_delivered[lane] for lane in range(2)]
        reward = (
            sum(step_delivered)
            - 0.02 * (sum(queues_after) + sum(buffers_after))
            - 0.01 * step_energy - step_charge
        )
        decisions = []
        for agent in range(4):
            if offset == 0:
                previous = 6
                current = selected if agent == 0 else 6
                age_before = 8
                kind = "DISCRETIONARY" if agent == 0 else "NONE"
                decision_charge = step_charge if agent == 0 else 0.0
            else:
                previous = selected_options[agent]
                current = previous
                age_before = ages_after[agent] + 1
                kind = "NONE"
                decision_charge = 0.0
            decision = _decision(
                agent, previous=previous, selected=current, charge=decision_charge,
                age_before=age_before, kind=kind,
            )
            decisions.append(decision)
            selected_options[agent] = current
            ages_after[agent] = int(decision["age_after_decision"])
        deployable_offset = 4 if (
            tape.spec.event.value == "COMMON-SENSOR" and event_active
        ) else 0
        steps.append({
            "primitive_time": boundary_time + offset,
            "k": 8,
            "event_active": event_active,
            "physical_queues_before": list(queues),
            "deployable_queues_before": [
                min(64, value + deployable_offset) for value in queues
            ],
            "buffers_before": list(buffers),
            "arrivals": arrivals,
            "relay_capacity": relay_capacity,
            "tracked": [0, 0],
            "delivered": step_delivered,
            "overflow": 0,
            "energy_spent": step_energy,
            "decision_charge": step_charge,
            "reward": reward,
            "physical_queues_after": list(queues_after),
            "buffers_after": list(buffers_after),
            "decisions": decisions,
        })
        queues = queues_after
        buffers = buffers_after
    terminal_potential = -0.02 * (sum(queues) + sum(buffers))
    base_numerator = sum(
        (0.99 ** offset) * float(step["reward"])
        for offset, step in enumerate(steps)
    ) + (0.99 ** 16) * terminal_potential
    energy_adjustment = (base_numerator - target_g16 * denominator) / 0.01
    assert energy_adjustment >= 0.0
    steps[0]["energy_spent"] = energy_adjustment
    steps[0]["reward"] = float(steps[0]["reward"]) - 0.01 * energy_adjustment
    return {
        "printed_index": printed_index,
        "action": ACTION_ORDER[printed_index],
        "selected_option": selected,
        "intervention_charge": charge,
        "intervention_charge_step": 0,
        "g16": target_g16,
        "steps": steps,
        "terminal_state": {
            "primitive_time": boundary_time + 16,
            "queues": list(queues),
            "buffers": list(buffers),
            "locations": [0, 1, 1, 2],
            "energies": [32.0, 32.0, 32.0, 32.0],
            "options": [selected, 6, 6, 6],
            "option_ages": [value + 1 for value in ages_after],
            "current_k": 8,
            "terminal_potential": terminal_potential,
        },
    }


def _observation(slot: int, episode: int, material: str) -> dict[str, object]:
    tape = census._expected_tape(slot, episode)
    cost = float(tape.spec.replanning_cost)
    denominator = int(tape.total_physical_arrivals())
    replacement_g16 = {"KEEP": -0.02, "MIDDLE": 0.0, "REPLAN": 0.02}[material]
    boundary_time = 80
    boundary = {
        "row_present": True,
        "scripted_history_transitions": boundary_time,
        "primitive_time": boundary_time,
        "environment_slot": 0,
        "elapsed_horizon": 8,
        "previous_option": 6,
        "legal_mask": [True, True, False, False, False, False, False, False],
        "g16": [0.0, replacement_g16, None, None, None, None, None, None],
        "denominator": denominator,
        "branches": [
            _branch(
                printed_index=0, boundary_time=boundary_time, cost=cost,
                denominator=denominator, target_g16=0.0, tape=tape,
            ),
            _branch(
                printed_index=1, boundary_time=boundary_time, cost=cost,
                denominator=denominator, target_g16=replacement_g16, tape=tape,
            ),
        ],
        "keep_g16": 0.0,
        "max_replacement_g16": replacement_g16,
        "maximizing_replacement": 1,
        "advantage": replacement_g16,
        "material_class": material,
    }
    return {
        "format": census.OBSERVATION_FORMAT,
        "object_id": census.SUPPORT_CENSUS_OBJECT_ID,
        "rng_namespace": census.SUPPORT_CENSUS_RNG_NAMESPACE,
        "slot": slot,
        "split": "EVALUATION",
        "regime": "K8",
        "episode_index": episode,
        "population_ordinal": slot * 64 + episode - 832,
        "spec": census._spec_record(tape),
        "boundary_scan": census._boundary_scan_record(boundary),
        "boundary": boundary,
    }


def _resource_receipt() -> dict[str, object]:
    floor = 4 * 1024**3
    return {
        "schema_version": 1,
        "minimum_available_bytes": floor,
        "available_physical_bytes": floor,
        "effective_available_bytes": floor,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }


def _run_receipt() -> dict[str, object]:
    floor = 4 * 1024**3
    return {
        "direction_id": "commitment_residual_triggered_options",
        "run_id": census.SUPPORT_CENSUS_LAUNCH_RUN_ID,
        "workers": 1,
        "threads_per_worker": 1,
        "minimum_available_bytes": floor,
        "estimate": {
            "wall_seconds": 7200.0,
            "peak_memory_gib": 2.0,
            "basis": "CRTO prospective frozen one-worker CPU envelope",
        },
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "memory_floor_pass": True,
        "memory_safe": True,
    }


def _runtime(observations: list[dict[str, object]]) -> dict[str, object]:
    branches = sum(
        len(row["boundary"]["branches"])
        for row in observations if row["boundary"]["row_present"]
    )
    transitions = sum(row["boundary"]["scripted_history_transitions"] for row in observations)
    base = 512 * 256
    common = 16 * branches
    return {
        "workers": 1,
        "threads_per_worker": 1,
        "base_episode_count": 1024,
        "charged_base_primitive_team_steps": 2 * base,
        "scripted_history_transitions": 2 * transitions,
        "actual_common_future_branch_count": 2 * branches,
        "actual_common_future_steps": 2 * common,
        "materialization_base_episode_count": 512,
        "materialization_charged_base_primitive_team_steps": base,
        "materialization_scripted_history_transitions": transitions,
        "materialization_common_future_branch_count": branches,
        "materialization_common_future_steps": common,
        "validation_base_episode_count": 512,
        "validation_charged_base_primitive_team_steps": base,
        "validation_scripted_history_transitions": transitions,
        "validation_common_future_branch_count": branches,
        "validation_common_future_steps": common,
        "actual_total_charged_primitive_team_steps": 2 * base + 2 * common,
        "primitive_team_step_ceiling": SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
        "wall_seconds": 1.0,
        "wall_ceiling_seconds": 7200,
        "peak_rss_bytes": 1,
        "peak_rss_ceiling_bytes": 2 * 1024**3,
        "cpu_seconds": 0.5,
        "cpu_occupancy_fraction": 0.5,
        "scratch_high_water_bytes": 0,
        "durable_high_water_bytes": 0,
        "io_read_bytes": 0,
        "io_write_bytes": 0,
        "measurement_cutoff": census.RUNTIME_MEASUREMENT_CUTOFF,
        "commit_tail_excluded": True,
        "commit_headroom": dict(census.COMMIT_HEADROOM),
        "final_candidate_staging_rehearsal_observed": {
            "wall_seconds": 0.5,
            "cpu_seconds": 0.25,
            "peak_rss_bytes": 1,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
        },
    }


def _independent_replay() -> dict[str, object]:
    count = 512
    per_tape = sum(
        int(item["raw_byte_length"]) for item in census.TAPE_ARRAY_INVENTORY
    )
    return {
        "mode": census.INDEPENDENT_REPLAY_MODE,
        "rebuilt_tapes": count,
        "scenario_spec_direct_matches": count,
        "array_raw_byte_direct_matches": count * len(census.TAPE_ARRAY_INVENTORY),
        "raw_bytes_compared_per_side": count * per_tape,
        "complete_boundary_provenance_direct_matches": count,
        "tape_array_inventory": [dict(item) for item in census.TAPE_ARRAY_INVENTORY],
    }


def _population(material_for: object) -> list[dict[str, object]]:
    return [
        _observation(slot, episode, material_for(slot, episode))
        for slot in range(8)
        for episode in range(832, 896)
    ]


def test_disposition_priority_is_mutually_exclusive() -> None:
    def summaries(keep: list[int], replan: list[int]) -> list[dict[str, object]]:
        return [
            {"counts": {"KEEP": keep[slot], "MIDDLE": 64 - keep[slot] - replan[slot],
                        "REPLAN": replan[slot]}}
            for slot in range(8)
        ]

    assert census._disposition(summaries([0] * 8, [64] * 8)) == census.DISPOSITION_NO_KEEP
    assert census._disposition(summaries([1] + [8] * 7, [8] * 8)) == census.DISPOSITION_KEEP_MINIMUM_FAIL
    assert census._disposition(summaries([8] * 8, [7] + [8] * 7)) == census.DISPOSITION_REPLAN_MINIMUM_FAIL
    assert census._disposition(summaries([8] * 8, [8] * 8)) == census.DISPOSITION_FEASIBLE


def test_complete_synthetic_population_summarizes_and_rejects_tampering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    rows = _population(lambda _slot, episode: "KEEP" if episode == 832 else "REPLAN")
    payload = census.summarize_support_census(
        rows,
        independent_replay=_independent_replay(),
        resource_receipt=_resource_receipt(),
        run_resource_receipt=_run_receipt(),
        runtime=_runtime(rows),
    )
    assert [summary["counts"]["KEEP"] for summary in payload["slot_summaries"]] == [1] * 8
    # One witness in every slot is constructive but below the frozen minimum.
    assert payload["disposition"] == census.DISPOSITION_KEEP_MINIMUM_FAIL
    assert len(payload["keep_witnesses"]) == 8
    assert census.validate_support_census(payload) == payload

    boundaries_by_tape = {
        (
            int(row["spec"]["episode_seed"]), int(row["episode_index"]),
        ): deepcopy(row["boundary"])
        for row in rows
    }

    class ReplayLedger:
        def __init__(self) -> None:
            self.started = False
            self.count = 0

        def begin_validation_replay(self) -> None:
            self.started = True

        def record_validation_base_episode(self, _steps: int) -> None:
            assert self.started
            self.count += 1

        def finish_validation_replay(self) -> None:
            assert self.count == 512

    original_build = census.build_balanced_tapes
    rebuild_slots: list[int] = []

    def independent_build(*, replicate: int, **kwargs):
        rebuild_slots.append(replicate)
        return original_build(replicate=replicate, **kwargs)

    monkeypatch.setattr(census, "build_balanced_tapes", independent_build)
    monkeypatch.setattr(
        census,
        "materialize_support_boundary_provenance",
        lambda tape, **_kwargs: deepcopy(boundaries_by_tape[(
            int(tape.spec.episode_seed), int(tape.spec.episode_index),
        )]),
    )
    assert census.validate_support_full_replay(
        rows, ledger=ReplayLedger(),
    ) == _independent_replay()
    assert rebuild_slots == list(range(8))
    monkeypatch.setattr(
        census,
        "materialize_support_boundary_provenance",
        lambda *_args, **_kwargs: pytest.fail("pure receipt validation reached host/G16"),
    )
    monkeypatch.setattr(
        census,
        "build_balanced_tapes",
        lambda **_kwargs: pytest.fail("pure receipt validation rebuilt a tape"),
    )
    assert census.validate_support_census(payload) == payload
    census.publish_support_census_create_only(
        tmp_path / "pure-direction", tmp_path / "pure-external.json", payload,
    )

    mutated = deepcopy(payload)
    mutated["activity"]["optimizer_updates"] = 1
    with pytest.raises(census.SupportCensusError, match="activity"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    mutated["independent_replay"]["array_raw_byte_direct_matches"] -= 1
    with pytest.raises(census.SupportCensusError, match="independent full replay"):
        census.validate_support_census(mutated)

    for field, bad_value in (
        ("direction_id", "another_direction"),
        ("run_id", "wrong_support_run"),
    ):
        mutated = deepcopy(payload)
        mutated["run_resource_receipt"][field] = bad_value
        with pytest.raises(census.SupportCensusError, match="launch"):
            census.validate_support_census(mutated)
    mutated = deepcopy(payload)
    mutated["run_resource_receipt"]["estimate"]["basis"] = "generic envelope"
    with pytest.raises(census.SupportCensusError, match="launch"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    mutated["observations"][0]["boundary"]["denominator"] += 1
    with pytest.raises(census.SupportCensusError, match="denominator|G16"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    mutated["observations"][0]["boundary"]["branches"][0]["steps"][0]["arrivals"][0] += 1
    with pytest.raises(census.SupportCensusError, match="transition arithmetic"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    mutated["observations"][0]["boundary_scan"]["primitive_time"] += 4
    with pytest.raises(census.SupportCensusError, match="boundary scan"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    mutated["observations"][0]["boundary"]["branches"][1]["steps"][0][
        "decisions"
    ][1]["kind"] = "DISCRETIONARY"
    with pytest.raises(census.SupportCensusError, match="share one predecision state"):
        census.validate_support_census(mutated)

    mutated = deepcopy(payload)
    row = mutated["observations"][0]
    step = row["boundary"]["branches"][1]["steps"][5]
    step["event_active"] = not step["event_active"]
    deployable_offset = 4 if (
        row["spec"]["event"] == "COMMON-SENSOR" and step["event_active"]
    ) else 0
    step["deployable_queues_before"] = [
        min(64, value + deployable_offset) for value in step["physical_queues_before"]
    ]
    with pytest.raises(census.SupportCensusError, match="share one predecision state"):
        census.validate_support_census(mutated)


def test_namespace_mismatch_is_rejected_before_boundary_execution() -> None:
    unrelated_tape = build_balanced_tapes(
        replicate=0, split=Split.EVALUATION, regime="K8", count=64,
        first_episode_index=832, rng_namespace=2_026_083_193,
    )[0]
    with pytest.raises(census.SupportCensusError, match="namespace"):
        census.materialize_support_observation(unrelated_tape, slot=0)


def test_create_only_publishes_byte_identical_receipts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    payload = {"small": "validated"}
    monkeypatch.setattr(census, "validate_support_census", lambda value: dict(value))
    output = tmp_path / "direction"
    result = tmp_path / "external.json"
    assert census.publish_support_census_create_only(output, result, payload) == payload
    receipt = output / "support_census_receipt.json"
    assert receipt.read_bytes() == result.read_bytes()
    marker = json.loads((output / census.PUBLICATION_MARKER_NAME).read_text(encoding="utf-8"))
    assert marker["complete"] is True
    assert marker["commit_law"] == "EXTERNAL_RESULT_FIRST_DIRECTION_ROOT_SECOND"
    assert json.loads(result.read_text(encoding="utf-8")) == payload
    with pytest.raises(FileExistsError):
        census.publish_support_census_create_only(output, result, payload)
