from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
    support_census as census,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    SUPPORT_CENSUS_CONSUMED_ATTEMPT,
    SUPPORT_CENSUS_FRESH_EXECUTION_ENABLED,
    SUPPORT_CENSUS_LIFECYCLE,
    SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
    SUPPORT_CENSUS_TERMINAL_DISPOSITION,
    SupportCensusConsumedError,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    ACTION_ORDER,
)


EVENTS = (
    "NONE", "UNANNOUNCED-DIFFERENTIAL", "CUED-DIFFERENTIAL", "COMMON-SENSOR",
)
ONSETS = (50, 66, 82, 98, 146, 162, 178, 194)
CELLS = tuple(product(EVENTS, (0.25, 4.0), ONSETS))


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
    target_g16: float,
) -> dict[str, object]:
    selected = 6 if printed_index == 0 else printed_index - 1
    charge = 0.0 if printed_index == 0 else 0.05 + cost
    queues = [0, 0]
    buffers = [32, 32]
    selected_options = [selected, 6, 6, 6]
    ages_after = [0 if selected != 6 else 8, 8, 8, 8]
    steps: list[dict[str, object]] = []
    for offset in range(16):
        arrivals = [1, 0]
        relay_capacity = [1, 1]
        step_charge = charge if offset == 0 else 0.0
        delivered = [1, 1]
        queues_after = [queues[0] + 1, queues[1]]
        buffers_after = [buffers[0] - 1, buffers[1] - 1]
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
        reward = (
            sum(delivered) - 0.02 * (sum(queues_after) + sum(buffers_after))
            - step_charge
        )
        steps.append({
            "primitive_time": boundary_time + offset,
            "k": 8,
            "event_active": False,
            "physical_queues_before": list(queues),
            "deployable_queues_before": list(queues),
            "buffers_before": list(buffers),
            "arrivals": arrivals,
            "relay_capacity": relay_capacity,
            "tracked": [0, 0],
            "delivered": delivered,
            "overflow": 0,
            "energy_spent": 0.0,
            "decision_charge": step_charge,
            "reward": reward,
            "physical_queues_after": list(queues_after),
            "buffers_after": list(buffers_after),
            "decisions": decisions,
        })
        queues, buffers = queues_after, buffers_after
    terminal_potential = -0.02 * (sum(queues) + sum(buffers))
    numerator = sum(
        (0.99 ** offset) * float(step["reward"])
        for offset, step in enumerate(steps)
    ) + (0.99 ** 16) * terminal_potential
    adjustment = (numerator - target_g16 * denominator) / 0.01
    assert adjustment >= 0.0
    steps[0]["energy_spent"] = adjustment
    steps[0]["reward"] = float(steps[0]["reward"]) - 0.01 * adjustment
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
            "queues": queues,
            "buffers": buffers,
            "locations": [0, 1, 1, 2],
            "energies": [32.0, 32.0, 32.0, 32.0],
            "options": selected_options,
            "option_ages": [value + 1 for value in ages_after],
            "current_k": 8,
            "terminal_potential": terminal_potential,
        },
    }


def _observation(slot: int, offset: int) -> dict[str, object]:
    episode = 832 + offset
    event, cost, onset = CELLS[offset]
    denominator = 512
    keep_g16 = -0.05
    replacement_g16 = -0.03
    advantage = replacement_g16 - keep_g16
    boundary_time = 20
    boundary = {
        "row_present": True,
        "scripted_history_transitions": boundary_time,
        "primitive_time": boundary_time,
        "environment_slot": 0,
        "elapsed_horizon": 8,
        "previous_option": 6,
        "legal_mask": [True, True, False, False, False, False, False, False],
        "g16": [keep_g16, replacement_g16, None, None, None, None, None, None],
        "denominator": denominator,
        "branches": [
            _branch(
                printed_index=0, boundary_time=boundary_time, cost=cost,
                denominator=denominator, target_g16=keep_g16,
            ),
            _branch(
                printed_index=1, boundary_time=boundary_time, cost=cost,
                denominator=denominator, target_g16=replacement_g16,
            ),
        ],
        "keep_g16": keep_g16,
        "max_replacement_g16": replacement_g16,
        "maximizing_replacement": 1,
        "advantage": advantage,
        "material_class": "REPLAN",
    }
    return {
        "format": census.OBSERVATION_FORMAT,
        "object_id": census.SUPPORT_CENSUS_OBJECT_ID,
        "rng_namespace": census.SUPPORT_CENSUS_RNG_NAMESPACE,
        "slot": slot,
        "split": "EVALUATION",
        "regime": "K8",
        "episode_index": episode,
        "population_ordinal": slot * 64 + offset,
        "spec": {
            "episode_index": episode,
            "episode_seed": 10_000_000 + slot * 10_000 + episode,
            "regime": "K8",
            "event": event,
            "event_onset": onset,
            "replanning_cost": cost,
        },
        "boundary_scan": {
            "row_present": True,
            "scripted_history_transitions": boundary_time,
            "primitive_time": boundary_time,
            "environment_slot": 0,
            "elapsed_horizon": 8,
            "previous_option": 6,
            "legal_printed_indices": [0, 1],
        },
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


@pytest.fixture(scope="module")
def consumed_payload() -> dict[str, object]:
    observations = [_observation(slot, offset) for slot in range(8) for offset in range(64)]
    branches = 2 * len(observations)
    transitions = 20 * len(observations)
    base = 512 * 256
    common = 16 * branches
    cells = {
        f"h{elapsed}/cost{cost:.2f}": (32 if elapsed == 8 else 0)
        for elapsed in (4, 8, 12, 16) for cost in (0.25, 4.0)
    }
    slot_summaries = [{
        "slot": slot,
        "assigned_tapes": 64,
        "retained_boundaries": 64,
        "absent_boundaries": 0,
        "counts": {"KEEP": 0, "MIDDLE": 0, "REPLAN": 64},
        "advantage_extrema": {
            "minimum": observations[0]["boundary"]["advantage"],
            "maximum": observations[0]["boundary"]["advantage"],
        },
        "elapsed_horizon_cost_cell_counts": dict(cells),
        "common_future_branches": 128,
    } for slot in range(8)]
    replay = {
        "mode": census.INDEPENDENT_REPLAY_MODE,
        "rebuilt_tapes": 512,
        "scenario_spec_direct_matches": 512,
        "array_raw_byte_direct_matches": 512 * len(census.TAPE_ARRAY_INVENTORY),
        "raw_bytes_compared_per_side": 512 * sum(
            int(item["raw_byte_length"]) for item in census.TAPE_ARRAY_INVENTORY
        ),
        "complete_boundary_provenance_direct_matches": 512,
        "tape_array_inventory": [dict(item) for item in census.TAPE_ARRAY_INVENTORY],
    }
    runtime = {
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
    return {
        "format": census.FORMAT,
        "object_id": census.SUPPORT_CENSUS_OBJECT_ID,
        "rng_namespace": census.SUPPORT_CENSUS_RNG_NAMESPACE,
        "claim_ceiling": census.SUPPORT_CENSUS_CLAIM_CEILING,
        "slots": list(range(8)),
        "split": "EVALUATION",
        "regime": "K8",
        "first_episode_index": 832,
        "episodes_per_slot": 64,
        "population_order": "SLOT_THEN_EPISODE_INDEX",
        "selection_law": census.SELECTION_LAW,
        "material_advantage_threshold": 0.02,
        "minimum_rows_per_material_stratum": 8,
        "slot_summaries": slot_summaries,
        "global_counts": {"KEEP": 0, "MIDDLE": 0, "REPLAN": 512},
        "global_advantage_extrema": slot_summaries[0]["advantage_extrema"],
        "keep_witnesses": [],
        "observations": observations,
        "independent_replay": replay,
        "disposition": SUPPORT_CENSUS_TERMINAL_DISPOSITION,
        "resource_receipt": _resource_receipt(),
        "run_resource_receipt": _run_receipt(),
        "runtime": runtime,
        "performance": {
            "disposition": "PILOT_ONLY",
            "bounded_support_census_only": True,
            "raw_pilot_object": False,
            "reason": census.PERFORMANCE_REASON,
        },
        "activity": {
            "support_tapes_materialized": 1024,
            "support_boundaries_materialized": 1024,
            "materialization_support_tapes": 512,
            "validation_support_tapes": 512,
            "materialization_support_boundaries": 512,
            "validation_support_boundaries": 512,
            "common_future_rollouts": 2 * branches,
            "materialization_common_future_rollouts": branches,
            "validation_common_future_rollouts": branches,
            "learner_models_constructed": 0,
            "predictor_models_constructed": 0,
            "gate_models_constructed": 0,
            "optimizer_updates": 0,
            "checkpoints": 0,
            "true_residual_activity": 0,
            "deranged_activity": 0,
            "final_namespace_reads": 0,
            "pilot_namespace_reads": 0,
        },
    }


def test_tombstone_constants_and_surface_are_terminal() -> None:
    assert census.support_census_tombstone() == {
        "object_id": census.SUPPORT_CENSUS_OBJECT_ID,
        "lifecycle": "TERMINAL_CONSUMED",
        "terminal_disposition": "CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET",
        "consumed_attempt": ".2",
        "fresh_execution_enabled": False,
        "reason": census.SUPPORT_CENSUS_TOMBSTONE_REASON,
    }
    assert SUPPORT_CENSUS_LIFECYCLE == "TERMINAL_CONSUMED"
    assert SUPPORT_CENSUS_CONSUMED_ATTEMPT == ".2"
    assert SUPPORT_CENSUS_FRESH_EXECUTION_ENABLED is False
    assert set(census.__all__) == {
        "SupportCensusConsumedError", "SupportCensusError",
        "load_consumed_support_census", "support_census_tombstone",
        "validate_support_census",
    }


def test_existing_receipt_validator_and_loader_remain_read_only(
    consumed_payload: dict[str, object], tmp_path: Path,
) -> None:
    assert census.validate_support_census(consumed_payload) == consumed_payload
    artifact = tmp_path / "consumed.json"
    artifact.write_text(json.dumps(consumed_payload), encoding="utf-8")
    before = {path: path.stat().st_size for path in tmp_path.iterdir()}
    assert census.load_consumed_support_census(artifact) == consumed_payload
    after = {path: path.stat().st_size for path in tmp_path.iterdir()}
    assert after == before


def test_read_only_validator_import_does_not_load_preflight_builder_or_host() -> None:
    package = (
        "experiments.candidates."
        "commitment_residual_triggered_options_common_history_gate_r01"
    )
    code = (
        "import sys\n"
        f"from {package} import support_census\n"
        "forbidden = (\n"
        f"    '{package}.preflight',\n"
        f"    '{package}.host_bridge',\n"
        "    'experiments.candidates.commitment_residual_triggered_options.host',\n"
        ")\n"
        "loaded = [name for name in forbidden if name in sys.modules]\n"
        "assert not loaded, loaded\n"
    )
    repository_root = Path(census.__file__).resolve().parents[3]
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_host_bridge_support_materializer_is_a_zero_effect_tombstone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
        host_bridge,
    )

    monkeypatch.setattr(
        host_bridge, "_locate_common_history_boundary",
        lambda _tape: pytest.fail("support materializer reached host boundary scan"),
    )
    monkeypatch.setattr(
        host_bridge, "common_future_audit_rollout",
        lambda *_args, **_kwargs: pytest.fail("support materializer reached G16"),
    )
    poison = _Unreadable()
    before = list(tmp_path.iterdir())
    with pytest.raises(SupportCensusConsumedError):
        host_bridge.materialize_support_boundary_provenance(poison, ledger=poison)
    assert list(tmp_path.iterdir()) == before


class _Unreadable:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"consumed seam inspected argument attribute {name}")

    def __iter__(self):
        raise AssertionError("consumed seam iterated an argument")

    def __len__(self) -> int:
        raise AssertionError("consumed seam measured an argument")

    def __getitem__(self, key: object) -> object:
        raise AssertionError(f"consumed seam indexed an argument at {key!r}")


@pytest.mark.parametrize(
    "invoke",
    (
        lambda poison: census._expected_tapes(poison),
        lambda poison: census._expected_tape(poison, poison),
        lambda poison: census.registered_support_tapes(poison),
        lambda poison: census.materialize_support_observation(poison, slot=poison, ledger=poison),
        lambda poison: census.validate_support_full_replay(poison, ledger=poison),
        lambda poison: census.summarize_support_census(
            poison, independent_replay=poison, resource_receipt=poison,
            run_resource_receipt=poison, runtime=poison,
        ),
        lambda poison: census.prepare_support_census_publication(poison, poison, poison),
        lambda poison: census.discard_prepared_support_publication(poison),
        lambda poison: census.commit_prepared_support_publication(poison),
        lambda poison: census.publish_support_census_create_only(
            poison, poison, poison, before_commit=poison,
        ),
    ),
)
def test_every_execution_and_publication_seam_rejects_before_argument_access(
    invoke: object, tmp_path: Path,
) -> None:
    poison = _Unreadable()
    before = list(tmp_path.iterdir())
    with pytest.raises(SupportCensusConsumedError, match="valid attempt \\.2"):
        invoke(poison)
    assert list(tmp_path.iterdir()) == before
