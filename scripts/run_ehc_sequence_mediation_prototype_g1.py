"""Thin nonformal runner for the accepted G1 sequence-mediation prototype."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.ehc_sequence_mediation_g1 import (
    CONTROLLERS,
    analyze_prototype,
    collect_natural_episode,
    run_event_intervention,
    run_mark_intervention,
)
from ha_ctse_process.temporal_duty_g1 import HORIZON, make_episode_spec


ASSIGNMENT_ID = "EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1"
SOURCE_FAMILY = "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
SCHEMA_VERSION = 1
MAX_SNAPSHOTS_PER_EPISODE = 2
SEQUENCE_WINDOW = 6
EPISODES_PER_CONTROLLER = 32
TOTAL_NATURAL_EPISODES = 192
DESIGN_PATH = "docs/research/designs/EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1.md"
SOURCE_PATHS = (
    DESIGN_PATH,
    "ha_ctse_process/temporal_duty_g1.py",
    "ha_ctse_process/ehc_sequence_mediation_g1.py",
    "scripts/run_ehc_sequence_mediation_prototype_g1.py",
)
SEED_INVENTORY = {
    "task": 731001,
    "membership": 731002,
    "duty": 731003,
    "opportunity": 731004,
    "event": 731005,
    "mark": 731006,
    "action": 731007,
    "evaluation": 731008,
    "audit": 731009,
}
_MEASUREMENT_FAMILIES = (
    "policy_dependence",
    "instantaneous_tv",
    "sequence_hamming",
    "terminal_utility_delta",
    "natural_mediation",
    "heldout_robustness",
)
_COMMON_ARTIFACT_KEYS = {
    "schema_version",
    "formal",
    "conclusion_bearing",
    "assignment_id",
    "source_family",
    "design_identity",
    "source_identity",
    "seed_inventory",
    "runtime_provenance",
    "cell_inventory",
    "records_sha256",
}
_MANIFEST_KEYS = _COMMON_ARTIFACT_KEYS | {
    "artifact_kind",
    "status",
    "total_natural_episodes",
    "episodes_per_controller",
    "maximum_snapshots_per_episode",
    "maximum_intervention_pairs_per_kind",
    "analysis_sha256",
}
_ANALYSIS_KEYS = _COMMON_ARTIFACT_KEYS | {
    "artifact_kind",
    "status",
    "measurement_tuple",
    "controller_provenance",
}


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    source_commit = completed.stdout.strip().lower()
    if len(source_commit) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit
    ):
        raise RuntimeError("source commit is not a full lowercase Git SHA")
    return source_commit


def current_source_identity() -> dict[str, object]:
    files = [
        {"path": relative_path, "sha256": _file_sha256(PROJECT_ROOT / relative_path)}
        for relative_path in SOURCE_PATHS
    ]
    return {
        "source_commit": _git_source_commit(),
        "files": files,
        "bundle_sha256": _canonical_sha256(files),
    }


def current_design_identity() -> dict[str, str]:
    return {
        "assignment_id": ASSIGNMENT_ID,
        "path": DESIGN_PATH,
        "sha256": _file_sha256(PROJECT_ROOT / DESIGN_PATH),
    }


def current_runtime_provenance() -> dict[str, object]:
    if os.environ.get("OMP_NUM_THREADS") != "1":
        raise RuntimeError("OMP_NUM_THREADS must be exactly 1")
    if os.environ.get("MKL_NUM_THREADS") != "1":
        raise RuntimeError("MKL_NUM_THREADS must be exactly 1")

    import torch

    if torch.cuda.is_available():
        raise RuntimeError("this prototype requires the CPU-only runtime")
    if torch.get_num_threads() != 1:
        raise RuntimeError("PyTorch intra-op thread count must be exactly 1")
    executable = Path(sys.executable).resolve()
    expected_executable = Path(
        "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
    ).resolve()
    if executable != expected_executable:
        raise RuntimeError(
            "prototype must use C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
        )
    return {
        "backend": "cpu",
        "python_executable": executable.as_posix(),
        "torch_version": str(torch.__version__),
        "torch_num_threads": int(torch.get_num_threads()),
        "omp_num_threads": 1,
        "mkl_num_threads": 1,
    }


def enumerate_registered_cells() -> tuple[dict[str, object], ...]:
    cells: list[dict[str, object]] = []
    episode_index = 0
    for controller in CONTROLLERS:
        for split, durations in (("fitting", (6, 14)), ("heldout", (10, 18))):
            for roster_size in (2, 3):
                for duration in durations:
                    for sign_start in (-1, 1):
                        for rotation in (0, 1):
                            cells.append(
                                {
                                    "episode_index": episode_index,
                                    "controller": controller,
                                    "split": split,
                                    "roster_size": roster_size,
                                    "duration": duration,
                                    "sign_start": sign_start,
                                    "rotation": rotation,
                                }
                            )
                            episode_index += 1
    if len(cells) != TOTAL_NATURAL_EPISODES:
        raise RuntimeError("registered episode inventory size changed")
    return tuple(cells)


def _finite_tree(value: object) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(float(value))
    return True


def _validate_float_domain(
    value: object, *, lower: float, upper: float, label: str
) -> None:
    if type(value) is not float:
        raise ValueError(f"{label} must be an exact float")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    if not lower <= value <= upper:
        raise ValueError(f"{label} is outside its domain [{lower}, {upper}]")


def _validate_exact_dict(
    value: object, *, keys: set[str], label: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} schema differs")
    return value


def _validate_policy_dependence(value: object, *, label: str) -> None:
    policy = _validate_exact_dict(
        value,
        keys={
            "renew_given_new_segment",
            "renew_given_mid_segment",
            "difference",
            "commitment_lifetime_support",
        },
        label=label,
    )
    _validate_float_domain(
        policy["renew_given_new_segment"],
        lower=0.0,
        upper=1.0,
        label=f"{label} renew_given_new_segment",
    )
    _validate_float_domain(
        policy["renew_given_mid_segment"],
        lower=0.0,
        upper=1.0,
        label=f"{label} renew_given_mid_segment",
    )
    _validate_float_domain(
        policy["difference"],
        lower=-1.0,
        upper=1.0,
        label=f"{label} difference",
    )
    support = policy["commitment_lifetime_support"]
    if (
        not isinstance(support, list)
        or not support
        or any(type(lifetime) is not int for lifetime in support)
        or any(not 1 <= lifetime <= HORIZON for lifetime in support)
        or support != sorted(set(support))
    ):
        raise ValueError(
            f"{label} commitment lifetime support must be an exact sorted unique "
            f"positive int list within horizon {HORIZON}"
        )


def _validate_sequence_hamming(value: object, *, label: str) -> None:
    sequence = _validate_exact_dict(
        value,
        keys={"event_keep_vs_renew", "mark_current_vs_opposite"},
        label=label,
    )
    for contrast in ("event_keep_vs_renew", "mark_current_vs_opposite"):
        metrics = _validate_exact_dict(
            sequence[contrast],
            keys={"hamming", "correctness_difference"},
            label=f"{label} {contrast}",
        )
        _validate_float_domain(
            metrics["hamming"],
            lower=0.0,
            upper=1.0,
            label=f"{label} {contrast} hamming",
        )
        _validate_float_domain(
            metrics["correctness_difference"],
            lower=-1.0,
            upper=1.0,
            label=f"{label} {contrast} correctness_difference",
        )


def _validate_terminal_utility_delta(value: object, *, label: str) -> None:
    terminal = _validate_exact_dict(
        value,
        keys={"event_keep_vs_renew", "mark_current_vs_opposite"},
        label=label,
    )
    for contrast in ("event_keep_vs_renew", "mark_current_vs_opposite"):
        _validate_float_domain(
            terminal[contrast],
            lower=-1.0,
            upper=1.0,
            label=f"{label} {contrast}",
        )


def _validate_natural_mediation(value: object, *, label: str) -> None:
    natural = _validate_exact_dict(
        value,
        keys={
            "boundary_renew_rate",
            "mid_segment_keep_rate",
            "hidden_post_cue_correctness",
            "natural_utility",
        },
        label=label,
    )
    for metric in natural:
        _validate_float_domain(
            natural[metric],
            lower=0.0,
            upper=1.0,
            label=f"{label} {metric}",
        )


def _validate_measurement_value(family: str, value: object, *, label: str) -> None:
    if family == "policy_dependence":
        _validate_policy_dependence(value, label=label)
    elif family == "instantaneous_tv":
        _validate_float_domain(value, lower=0.0, upper=1.0, label=label)
    elif family == "sequence_hamming":
        _validate_sequence_hamming(value, label=label)
    elif family == "terminal_utility_delta":
        _validate_terminal_utility_delta(value, label=label)
    elif family == "natural_mediation":
        _validate_natural_mediation(value, label=label)
    else:
        raise ValueError(f"unsupported measurement family {family}")


def _record_cell(record: Mapping[str, object]) -> tuple[object, ...]:
    controller = record.get("controller")
    spec = record.get("spec")
    if controller not in CONTROLLERS or not isinstance(spec, Mapping):
        raise ValueError("record controller or spec is malformed")
    required = ("split", "roster_size", "duration", "sign_start", "rotation")
    if any(name not in spec for name in required):
        raise ValueError("record spec is missing registered cell fields")
    values = tuple(spec[name] for name in required)
    if type(values[0]) is not str or any(type(value) is not int for value in values[1:]):
        raise ValueError("record spec fields have noncanonical types")
    try:
        canonical = make_episode_spec(
            str(values[0]),
            int(values[1]),
            int(values[2]),
            int(values[3]),
            int(values[4]),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("record spec is not a registered cell") from error
    if (
        canonical.split,
        canonical.roster_size,
        canonical.duration,
        canonical.sign_start,
        canonical.rotation,
    ) != values:
        raise ValueError("record spec fields are not canonical")
    return (controller, *values)


def _validate_intervention(
    result: object, *, kind: str, controller: str, record_index: int
) -> None:
    if not isinstance(result, Mapping):
        raise ValueError(f"record {record_index} {kind} intervention is malformed")
    if result.get("kind") != kind or result.get("controller") != controller:
        raise ValueError(f"record {record_index} {kind} intervention identity is invalid")
    required_keys = {
        "kind",
        "controller",
        "snapshot_provenance",
        "target_slot",
        "contrast",
        "branch_origin_equal",
        "common_random_numbers",
        "branches",
        "metrics",
    }
    if not required_keys.issubset(result):
        raise ValueError(f"record {record_index} branch schema is incomplete")
    if type(result.get("target_slot")) is not int:
        raise ValueError(f"record {record_index} branch target slot is malformed")
    selection = result.get("snapshot_provenance")
    if not isinstance(selection, Mapping) or not {
        "time",
        "age",
        "cue_present",
        "remaining_active_opportunities",
        "terminal_event_same_step",
        "current_mark",
    }.issubset(selection):
        raise ValueError(f"record {record_index} branch snapshot provenance is malformed")
    expected_contrast = (
        {
            "left": {"event": "KEEP", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
        if kind == "event"
        else {
            "left": {"event": "RENEW", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
    )
    if result.get("contrast") != expected_contrast:
        raise ValueError(f"record {record_index} branch contrast differs")
    if result.get("branch_origin_equal") is not True:
        raise ValueError(f"record {record_index} branch origin equality is invalid")
    common_random_numbers = result.get("common_random_numbers")
    if (
        not isinstance(common_random_numbers, Mapping)
        or common_random_numbers.get("equal") is not True
        or common_random_numbers.get("left_draws")
        != common_random_numbers.get("right_draws")
    ):
        raise ValueError(f"record {record_index} branch RNG equality is invalid")
    metrics = result.get("metrics")
    required_metrics = {
        "instantaneous_tv",
        "sequence_hamming",
        "sequence_correctness_difference",
        "terminal_utility_delta",
    }
    if not isinstance(metrics, Mapping) or set(metrics) != required_metrics:
        raise ValueError(f"record {record_index} branch metrics are malformed")
    branches = result.get("branches")
    if not isinstance(branches, Mapping) or set(branches) != {"left", "right"}:
        raise ValueError(f"record {record_index} branch pair is malformed")
    branch_keys = {
        "intervention_event",
        "intervention_mark",
        "intervention_time",
        "intervention_action",
        "intervention_probabilities",
        "downstream_actions",
        "downstream_correct",
        "downstream_times",
        "terminal_time",
        "terminal_outcome",
        "final_rng_draws",
    }
    for side, branch in branches.items():
        if not isinstance(branch, Mapping) or not branch_keys.issubset(branch):
            raise ValueError(f"record {record_index} {side} branch schema is incomplete")
        actions = branch.get("downstream_actions")
        correct = branch.get("downstream_correct")
        times = branch.get("downstream_times")
        probabilities = branch.get("intervention_probabilities")
        if (
            not isinstance(actions, (list, tuple))
            or not isinstance(correct, (list, tuple))
            or not isinstance(times, (list, tuple))
            or not isinstance(probabilities, (list, tuple))
            or len(probabilities) != 3
            or len(actions) != len(correct)
            or len(actions) != len(times)
            or len(actions) > SEQUENCE_WINDOW
        ):
            raise ValueError(f"record {record_index} {side} branch support is malformed")
    if not _finite_tree(result):
        raise ValueError(f"record {record_index} branch contains a nonfinite value")


def validate_records(records: object) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    expected_cells = enumerate_registered_cells()
    if len(records) != len(expected_cells):
        raise ValueError("record inventory is incomplete or contains extra cells")

    observed: set[tuple[object, ...]] = set()
    normalized: list[dict[str, object]] = []
    for index, (record, expected) in enumerate(zip(records, expected_cells, strict=True)):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} is not a dict")
        cell = _record_cell(record)
        expected_cell = (
            expected["controller"],
            expected["split"],
            expected["roster_size"],
            expected["duration"],
            expected["sign_start"],
            expected["rotation"],
        )
        if cell != expected_cell:
            raise ValueError(f"record inventory order or cell identity differs at {index}")
        if cell in observed:
            raise ValueError(f"duplicate record inventory cell at {index}")
        observed.add(cell)
        if record.get("seeds") != SEED_INVENTORY:
            raise ValueError(f"record {index} seed inventory differs")

        rows = record.get("rows")
        snapshots = record.get("branch_snapshots")
        event_results = record.get("event_interventions")
        mark_results = record.get("mark_interventions")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"record {index} natural rows are malformed")
        if not all(
            isinstance(row, Mapping)
            and row.get("provenance") == "natural"
            and row.get("forced") is False
            for row in rows
        ):
            raise ValueError(f"record {index} natural row provenance is invalid")
        if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= MAX_SNAPSHOTS_PER_EPISODE:
            raise ValueError(f"record {index} branch snapshot count is outside the bound")
        for snapshot in snapshots:
            if (
                not isinstance(snapshot, Mapping)
                or snapshot.get("version") != 1
                or snapshot.get("controller") != record.get("controller")
                or type(snapshot.get("target_slot")) is not int
                or not isinstance(snapshot.get("environment_state"), Mapping)
                or not isinstance(snapshot.get("controller_state"), Mapping)
            ):
                raise ValueError(f"record {index} intervention snapshot is malformed")
            selection = snapshot.get("selection")
            if not isinstance(selection, Mapping) or not {
                "time",
                "age",
                "cue_present",
                "remaining_active_opportunities",
                "terminal_event_same_step",
                "current_mark",
            }.issubset(selection):
                raise ValueError(f"record {index} intervention snapshot selection is malformed")
            if (
                selection.get("age") != 3
                or selection.get("cue_present") is not False
                or selection.get("terminal_event_same_step") is not False
                or type(selection.get("remaining_active_opportunities")) is not int
                or int(selection["remaining_active_opportunities"]) < 2
                or selection.get("current_mark") not in (-1, 1)
            ):
                raise ValueError(f"record {index} intervention snapshot is ineligible")
        if (
            not isinstance(event_results, list)
            or not isinstance(mark_results, list)
            or len(event_results) != len(snapshots)
            or len(mark_results) != len(snapshots)
        ):
            raise ValueError(f"record {index} branch pair inventory is incomplete")
        controller = str(record["controller"])
        for result in event_results:
            _validate_intervention(
                result, kind="event", controller=controller, record_index=index
            )
        for result in mark_results:
            _validate_intervention(
                result, kind="mark", controller=controller, record_index=index
            )
        if not _finite_tree(record):
            raise ValueError(f"record {index} contains a nonfinite value")
        normalized.append(record)
    return normalized


def _cell_inventory(records: list[dict[str, object]]) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for expected, record in zip(enumerate_registered_cells(), records, strict=True):
        spec = make_episode_spec(
            str(expected["split"]),
            int(expected["roster_size"]),
            int(expected["duration"]),
            int(expected["sign_start"]),
            int(expected["rotation"]),
        )
        snapshot_count = len(record["branch_snapshots"])
        inventory.append(
            {
                **expected,
                "action_denominator": spec.action_denominator,
                "eligible_segment_denominator": spec.eligible_segment_denominator,
                "branch_snapshot_count": snapshot_count,
                "event_intervention_pair_count": len(record["event_interventions"]),
                "mark_intervention_pair_count": len(record["mark_interventions"]),
            }
        )
    return inventory


def _validate_analysis_result(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "status",
        "measurement_tuple",
        "controller_provenance",
    }:
        raise ValueError("measurement analyzer result schema is malformed")
    if value.get("status") != "COMPLETE":
        raise ValueError("measurement analyzer result is not complete")
    measurement_tuple = value.get("measurement_tuple")
    if not isinstance(measurement_tuple, dict) or set(measurement_tuple) != set(
        _MEASUREMENT_FAMILIES
    ):
        raise ValueError("measurement analyzer family inventory differs")
    controller_provenance = value.get("controller_provenance")
    if not isinstance(controller_provenance, dict) or set(controller_provenance) != set(CONTROLLERS):
        raise ValueError("measurement analyzer controller provenance is malformed")
    for controller, provenance in controller_provenance.items():
        if not isinstance(provenance, Mapping) or provenance != {
            "natural_provenance": "natural",
            "fitting_cells": 16,
            "heldout_cells": 16,
            "event_contrast": "KEEP/current_vs_RENEW/opposite",
            "mark_contrast": "RENEW/current_vs_RENEW/opposite",
        }:
            raise ValueError(
                f"measurement analyzer controller provenance differs for {controller}"
            )
    for family in _MEASUREMENT_FAMILIES[:-1]:
        family_value = measurement_tuple.get(family)
        if not isinstance(family_value, Mapping) or set(family_value) != set(CONTROLLERS):
            raise ValueError(f"measurement {family} controller inventory differs")
        for controller, controller_value in family_value.items():
            if not isinstance(controller_value, Mapping) or set(controller_value) != {
                "fitting",
                "heldout",
            }:
                raise ValueError(f"measurement {family} split inventory differs")
            for split in ("fitting", "heldout"):
                _validate_measurement_value(
                    family,
                    controller_value[split],
                    label=f"measurement {family}/{controller}/{split}",
                )
    heldout = measurement_tuple.get("heldout_robustness")
    if not isinstance(heldout, Mapping) or set(heldout) != set(CONTROLLERS):
        raise ValueError("measurement heldout robustness controller inventory differs")
    heldout_keys = set(_MEASUREMENT_FAMILIES[:-1])
    for controller, heldout_value in heldout.items():
        if not isinstance(heldout_value, Mapping) or set(heldout_value) != heldout_keys:
            raise ValueError("measurement heldout robustness schema differs")
        for family in _MEASUREMENT_FAMILIES[:-1]:
            if heldout_value[family] != measurement_tuple[family][controller]["heldout"]:
                raise ValueError(
                    f"measurement heldout robustness differs for {controller}/{family}"
                )
    if not _finite_tree(value):
        raise ValueError("measurement analyzer result contains a nonfinite value")
    return value


def build_artifacts(
    records: object,
    analyzer_result: object,
    *,
    runtime_provenance: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    validated_records = validate_records(records)
    validated_analysis = _validate_analysis_result(analyzer_result)
    runtime = dict(runtime_provenance or current_runtime_provenance())
    if not _finite_tree(runtime):
        raise ValueError("runtime provenance contains a nonfinite value")
    common = {
        "schema_version": SCHEMA_VERSION,
        "formal": False,
        "conclusion_bearing": False,
        "assignment_id": ASSIGNMENT_ID,
        "source_family": SOURCE_FAMILY,
        "design_identity": current_design_identity(),
        "source_identity": current_source_identity(),
        "seed_inventory": deepcopy(SEED_INVENTORY),
        "runtime_provenance": deepcopy(runtime),
        "cell_inventory": _cell_inventory(validated_records),
        "records_sha256": _canonical_sha256(validated_records),
    }
    analysis = {
        **deepcopy(common),
        "artifact_kind": "EHC_SEQUENCE_MEDIATION_PROTOTYPE_G1_ANALYSIS",
        "status": "COMPLETE",
        "measurement_tuple": deepcopy(validated_analysis["measurement_tuple"]),
        "controller_provenance": deepcopy(
            validated_analysis["controller_provenance"]
        ),
    }
    manifest = {
        **deepcopy(common),
        "artifact_kind": "EHC_SEQUENCE_MEDIATION_PROTOTYPE_G1_MANIFEST",
        "status": "COMPLETE",
        "total_natural_episodes": TOTAL_NATURAL_EPISODES,
        "episodes_per_controller": EPISODES_PER_CONTROLLER,
        "maximum_snapshots_per_episode": MAX_SNAPSHOTS_PER_EPISODE,
        "maximum_intervention_pairs_per_kind": (
            TOTAL_NATURAL_EPISODES * MAX_SNAPSHOTS_PER_EPISODE
        ),
        "analysis_sha256": _canonical_sha256(analysis),
    }
    validate_prototype_artifacts(manifest, analysis, records=validated_records)
    return manifest, analysis


def _validate_cell_inventory(value: object) -> None:
    if not isinstance(value, list) or len(value) != TOTAL_NATURAL_EPISODES:
        raise ValueError("cell inventory is incomplete or contains extra cells")
    expected_cells = enumerate_registered_cells()
    for index, (cell, expected) in enumerate(zip(value, expected_cells, strict=True)):
        if not isinstance(cell, Mapping):
            raise ValueError(f"cell inventory entry {index} is malformed")
        if any(cell.get(key) != expected_value for key, expected_value in expected.items()):
            raise ValueError(f"cell inventory identity differs at {index}")
        for key in (
            "action_denominator",
            "eligible_segment_denominator",
            "branch_snapshot_count",
            "event_intervention_pair_count",
            "mark_intervention_pair_count",
        ):
            if type(cell.get(key)) is not int:
                raise ValueError(f"cell inventory {key} is not an integer")
        count = int(cell["branch_snapshot_count"])
        if not 1 <= count <= MAX_SNAPSHOTS_PER_EPISODE:
            raise ValueError("cell inventory branch count is outside the registered bound")
        if (
            cell["event_intervention_pair_count"] != count
            or cell["mark_intervention_pair_count"] != count
        ):
            raise ValueError("cell inventory branch pair counts differ")
        spec = make_episode_spec(
            str(cell["split"]),
            int(cell["roster_size"]),
            int(cell["duration"]),
            int(cell["sign_start"]),
            int(cell["rotation"]),
        )
        if (
            cell["action_denominator"] != spec.action_denominator
            or cell["eligible_segment_denominator"]
            != spec.eligible_segment_denominator
        ):
            raise ValueError("cell inventory exogenous denominators differ")


def validate_prototype_artifacts(
    manifest: object,
    analysis: object,
    *,
    records: object | None = None,
) -> None:
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        raise ValueError("prototype manifest schema is malformed")
    if not isinstance(analysis, dict) or set(analysis) != _ANALYSIS_KEYS:
        raise ValueError("prototype analysis schema is malformed")
    if manifest.get("formal") is not False or analysis.get("formal") is not False:
        raise ValueError("formal must be exactly false for prototype artifacts")
    if (
        manifest.get("conclusion_bearing") is not False
        or analysis.get("conclusion_bearing") is not False
    ):
        raise ValueError("conclusion-bearing must be exactly false")
    if manifest.get("status") != "COMPLETE" or analysis.get("status") != "COMPLETE":
        raise ValueError("prototype artifact status is not complete")
    if manifest.get("assignment_id") != ASSIGNMENT_ID or analysis.get("assignment_id") != ASSIGNMENT_ID:
        raise ValueError("prototype assignment identity differs")
    if manifest.get("source_family") != SOURCE_FAMILY or analysis.get("source_family") != SOURCE_FAMILY:
        raise ValueError("prototype source family identity differs")
    if manifest.get("design_identity") != current_design_identity():
        raise ValueError("prototype design identity or hash differs")
    if analysis.get("design_identity") != manifest.get("design_identity"):
        raise ValueError("analysis design identity differs from manifest")
    if manifest.get("source_identity") != current_source_identity():
        raise ValueError("prototype source identity or hash differs")
    if analysis.get("source_identity") != manifest.get("source_identity"):
        raise ValueError("analysis source identity differs from manifest")
    if manifest.get("seed_inventory") != SEED_INVENTORY or analysis.get("seed_inventory") != SEED_INVENTORY:
        raise ValueError("prototype seed inventory differs")
    if manifest.get("runtime_provenance") != analysis.get("runtime_provenance"):
        raise ValueError("runtime provenance differs across artifacts")
    runtime = manifest.get("runtime_provenance")
    if not isinstance(runtime, Mapping):
        raise ValueError("runtime provenance is malformed")
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_num_threads") != 1
        or runtime.get("omp_num_threads") != 1
        or runtime.get("mkl_num_threads") != 1
    ):
        raise ValueError("runtime provenance is not CPU with one thread")
    if manifest.get("cell_inventory") != analysis.get("cell_inventory"):
        raise ValueError("cell inventory differs across artifacts")
    _validate_cell_inventory(manifest.get("cell_inventory"))
    if not _finite_tree(manifest) or not _finite_tree(analysis):
        raise ValueError("prototype artifacts must contain only finite values")
    _validate_analysis_result(
        {
            "status": analysis["status"],
            "measurement_tuple": analysis["measurement_tuple"],
            "controller_provenance": analysis["controller_provenance"],
        }
    )
    if manifest.get("total_natural_episodes") != TOTAL_NATURAL_EPISODES:
        raise ValueError("manifest natural episode count differs")
    if manifest.get("episodes_per_controller") != EPISODES_PER_CONTROLLER:
        raise ValueError("manifest per-controller episode count differs")
    if manifest.get("maximum_snapshots_per_episode") != MAX_SNAPSHOTS_PER_EPISODE:
        raise ValueError("manifest snapshot branch bound differs")
    if (
        manifest.get("maximum_intervention_pairs_per_kind")
        != TOTAL_NATURAL_EPISODES * MAX_SNAPSHOTS_PER_EPISODE
    ):
        raise ValueError("manifest branch pair budget differs")
    record_hash = manifest.get("records_sha256")
    if not isinstance(record_hash, str) or len(record_hash) != 64:
        raise ValueError("manifest record hash is malformed")
    if analysis.get("records_sha256") != record_hash:
        raise ValueError("analysis record hash differs from manifest")
    if records is not None:
        validated_records = validate_records(records)
        if _canonical_sha256(validated_records) != record_hash:
            raise ValueError("record content hash differs")
        if _cell_inventory(validated_records) != manifest["cell_inventory"]:
            raise ValueError("record-derived cell inventory differs")
    if manifest.get("analysis_sha256") != _canonical_sha256(analysis):
        raise ValueError("analysis content hash differs")


def _validate_expected_file_sha256(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"expected {label} SHA-256 must be exactly 64 lowercase hex")
    return value


def load_and_validate_prototype_artifacts(
    manifest_path: str | Path,
    analysis_path: str | Path,
    *,
    expected_manifest_sha256: str,
    expected_analysis_sha256: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Load the exact two artifacts only after trusted byte-hash verification."""

    trusted_manifest_sha256 = _validate_expected_file_sha256(
        expected_manifest_sha256, label="manifest"
    )
    trusted_analysis_sha256 = _validate_expected_file_sha256(
        expected_analysis_sha256, label="analysis"
    )
    manifest_file = Path(manifest_path)
    analysis_file = Path(analysis_path)
    if manifest_file.resolve() == analysis_file.resolve():
        raise ValueError("manifest and analysis paths must identify exact distinct files")

    manifest_bytes = manifest_file.read_bytes()
    analysis_bytes = analysis_file.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != trusted_manifest_sha256:
        raise ValueError("manifest file hash differs from trusted expected SHA-256")
    if hashlib.sha256(analysis_bytes).hexdigest() != trusted_analysis_sha256:
        raise ValueError("analysis file hash differs from trusted expected SHA-256")

    manifest = json.loads(manifest_bytes)
    analysis = json.loads(analysis_bytes)
    validate_prototype_artifacts(manifest, analysis)
    return manifest, analysis


def validate_conclusion_bearing_evidence(
    manifest: object,
    analysis: object,
    *,
    records: object | None = None,
) -> None:
    validate_prototype_artifacts(manifest, analysis, records=records)
    raise ValueError("nonformal prototype artifacts are not conclusion-bearing evidence")


def validate_formal_evidence(
    manifest: object,
    analysis: object,
    *,
    records: object | None = None,
) -> None:
    validate_prototype_artifacts(manifest, analysis, records=records)
    raise ValueError("nonformal prototype artifacts are not formal evidence")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            dict(payload),
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_prototype(output_dir: str | Path) -> tuple[dict[str, object], dict[str, object]]:
    output_path = Path(output_dir)
    runtime_provenance = current_runtime_provenance()
    records: list[dict[str, object]] = []
    for cell in enumerate_registered_cells():
        spec = make_episode_spec(
            str(cell["split"]),
            int(cell["roster_size"]),
            int(cell["duration"]),
            int(cell["sign_start"]),
            int(cell["rotation"]),
        )
        controller = str(cell["controller"])
        episode = collect_natural_episode(spec, controller, dict(SEED_INVENTORY))
        snapshots = episode.get("branch_snapshots")
        if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= MAX_SNAPSHOTS_PER_EPISODE:
            raise ValueError("natural episode branch snapshot count is outside the bound")
        episode["event_interventions"] = [
            run_event_intervention(snapshot, controller, window=SEQUENCE_WINDOW)
            for snapshot in snapshots
        ]
        episode["mark_interventions"] = [
            run_mark_intervention(snapshot, controller, window=SEQUENCE_WINDOW)
            for snapshot in snapshots
        ]
        records.append(episode)

    validate_records(records)
    analyzer_result = analyze_prototype(records)
    manifest, analysis = build_artifacts(
        records,
        analyzer_result,
        runtime_provenance=runtime_provenance,
    )
    _write_json(output_path / "prototype_analysis.json", analysis)
    _write_json(output_path / "prototype_manifest.json", manifest)
    return manifest, analysis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the bounded nonformal EHC sequence-mediation G1 prototype."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    run_prototype(arguments.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
