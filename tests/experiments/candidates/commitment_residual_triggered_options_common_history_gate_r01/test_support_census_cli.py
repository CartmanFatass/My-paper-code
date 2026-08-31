from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
    run as run_module,
    support_census as census_module,
    support_census_worker as worker_module,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
    SUPPORT_CENSUS_OBJECT_ID,
    SUPPORT_CENSUS_RNG_NAMESPACE,
)


def test_support_census_cli_exposes_only_fresh_path_inputs() -> None:
    parser = run_module.build_parser()
    parsed = parser.parse_args([
        "support-census",
        "--output-root", "direction-root",
        "--result", "external.json",
        "--resource-receipt", "memory.json",
        "--run-resource-receipt", "assessment.json",
    ])
    assert parsed.action == "support-census"
    assert parsed.output_root == Path("direction-root")
    assert SUPPORT_CENSUS_OBJECT_ID == "CRTO-K8-FIRST-BOUNDARY-SUPPORT-CENSUS-20260831-01"
    assert SUPPORT_CENSUS_RNG_NAMESPACE == 2_026_083_192
    assert SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS == 393_216
    with pytest.raises(SystemExit):
        parser.parse_args([
            "support-census",
            "--output-root", "o",
            "--result", "r",
            "--resource-receipt", "m",
            "--run-resource-receipt", "a",
            "--rng-namespace", "7",
        ])


def test_support_census_launcher_fixes_worker_environment_and_checks_publication(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["environment"] = kwargs["env"]
        output = Path(command[command.index("--output-root") + 1])
        result = Path(command[command.index("--result") + 1])
        output.mkdir(parents=True)
        encoded = (json.dumps({"complete": True}, sort_keys=True) + "\n").encode()
        (output / "support_census_receipt.json").write_bytes(encoded)
        (output / "PUBLICATION_COMPLETE.json").write_text(json.dumps({
            "format": "CRTO_SUPPORT_CENSUS_DUAL_PUBLICATION_V1",
            "object_id": SUPPORT_CENSUS_OBJECT_ID,
            "complete": True,
            "commit_law": "EXTERNAL_RESULT_FIRST_DIRECTION_ROOT_SECOND",
            "receipt": "support_census_receipt.json",
        }), encoding="utf-8")
        result.write_bytes(encoded)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    monkeypatch.setattr(census_module, "validate_support_census", lambda value: dict(value))
    payload = run_module._launch_support_census_worker(
        output_root=tmp_path / "direction",
        result_path=tmp_path / "external.json",
        resource_receipt_path=tmp_path / "memory.json",
        run_resource_receipt_path=tmp_path / "assessment.json",
    )
    assert payload == {"complete": True}
    command = observed["command"]
    assert command[:3] == [
        str(Path(__import__("sys").executable)),
        "-m",
        (
            "experiments.candidates."
            "commitment_residual_triggered_options_common_history_gate_r01."
            "support_census_worker"
        ),
    ]
    assert "--rng-namespace" not in command and "--slot" not in command
    environment = observed["environment"]
    assert environment["HMASD_CRTO_SUPPORT_CENSUS_WORKER"] == SUPPORT_CENSUS_OBJECT_ID
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert all(environment[name] == "1" for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ))


def test_worker_refuses_before_first_tape_when_fresh_memory_admission_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv(worker_module.WORKER_ENV, SUPPORT_CENSUS_OBJECT_ID)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        monkeypatch.setenv(name, "1")
    tape_activity = {"called": False}

    def refused(_path: Path):
        raise RuntimeError("synthetic memory refusal")

    def forbidden_tape_activity(**_kwargs):
        tape_activity["called"] = True
        raise AssertionError("tape construction crossed a failed admission")

    monkeypatch.setattr(worker_module, "create_shared_resource_receipt", refused)
    monkeypatch.setattr(worker_module, "registered_support_tapes", forbidden_tape_activity)
    output = tmp_path / "direction"
    result = tmp_path / "external.json"
    with pytest.raises(RuntimeError, match="synthetic memory refusal"):
        worker_module._run_registered_support_census(
            output_root=output,
            result_path=result,
            resource_receipt_path=tmp_path / "memory.json",
            run_resource_receipt_path=tmp_path / "assessment.json",
        )
    assert tape_activity["called"] is False
    assert not output.exists() and not result.exists()


def test_worker_embeds_final_candidate_rehearsal_and_has_no_postcommit_checks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv(worker_module.WORKER_ENV, SUPPORT_CENSUS_OBJECT_ID)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        monkeypatch.setenv(name, "1")
    events: list[str] = []

    def receipt(path: Path) -> dict[str, object]:
        path.write_text("{}\n", encoding="utf-8")
        return {"receipt": str(path)}

    def assessment(path: Path, *, run_id: str) -> dict[str, object]:
        path.write_text("{}\n", encoding="utf-8")
        return {"run_id": run_id}

    class FakeLedger:
        def __init__(self) -> None:
            self.snapshots = 0

        def record_base_episode(self, _steps: int) -> None:
            pass

        def runtime_record(self, **_kwargs) -> dict[str, object]:
            self.snapshots += 1
            events.append(f"snapshot:{self.snapshots}")
            return {
                "wall_seconds": float(self.snapshots),
                "cpu_seconds": 0.5 * self.snapshots,
                "peak_rss_bytes": 1024,
                "io_read_bytes": 100 * self.snapshots,
                "io_write_bytes": 200 * self.snapshots,
                "scratch_high_water_bytes": 0,
                "durable_high_water_bytes": 0,
            }

        def check_limits(self) -> None:
            events.append("limits")

    monkeypatch.setattr(worker_module, "create_shared_resource_receipt", receipt)
    monkeypatch.setattr(worker_module, "create_shared_run_assessment", assessment)
    monkeypatch.setattr(worker_module, "SupportCensusWorkLedger", FakeLedger)
    monkeypatch.setattr(worker_module, "registered_support_tapes", lambda _slot: tuple(range(64)))
    monkeypatch.setattr(
        worker_module,
        "materialize_support_observation",
        lambda _tape, **_kwargs: {"boundary": {"scripted_history_transitions": 1}},
    )
    monkeypatch.setattr(
        worker_module,
        "validate_support_full_replay",
        lambda _rows, **_kwargs: {"complete": True},
    )

    rehearsal_snapshots: list[dict[str, object]] = []

    def summarize(_rows, *, runtime, **_kwargs):
        replay = dict(runtime.get("final_candidate_staging_rehearsal_observed", {}))
        if replay:
            rehearsal_snapshots.append(replay)
        return {"runtime": dict(runtime), "complete": True}

    monkeypatch.setattr(worker_module, "summarize_support_census", summarize)

    def prepare(_output, _result, payload):
        events.append("prepare")
        return {"staged_bytes": 100, "payload": payload}

    monkeypatch.setattr(worker_module, "prepare_support_census_publication", prepare)
    monkeypatch.setattr(
        worker_module, "discard_prepared_support_publication",
        lambda _prepared: events.append("discard"),
    )
    def commit(prepared):
        events.append("commit")
        return prepared["payload"]

    monkeypatch.setattr(worker_module, "commit_prepared_support_publication", commit)
    payload = worker_module._run_registered_support_census(
        output_root=tmp_path / "direction",
        result_path=tmp_path / "external.json",
        resource_receipt_path=tmp_path / "memory.json",
        run_resource_receipt_path=tmp_path / "assessment.json",
    )
    assert payload["complete"] is True
    assert events[-1] == "commit"
    terminal_index = max(
        index for index, event in enumerate(events) if event.startswith("snapshot:")
    )
    assert events[terminal_index + 1:] == ["commit"]
    assert events.count("prepare") == 2
    assert events.count("discard") == 1
    assert rehearsal_snapshots[-1] == {
        "wall_seconds": 2.0,
        "cpu_seconds": 1.0,
        "peak_rss_bytes": 1024,
        "io_read_bytes": 200,
        "io_write_bytes": 400,
    }
