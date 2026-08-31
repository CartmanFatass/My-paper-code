from pathlib import Path
import ast
import json
import subprocess

import numpy as np
import pytest
import torch

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import config
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import pilot as pilot_module
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import run as run_module
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    _launch_production_worker, _launch_raw_pilot_worker, build_parser, run_registered,
    source_check,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.models import (
    CommonHistoryGate, FreshPredictor,
)


def test_contract_constants_rng_domains_and_ambient_state() -> None:
    assert config.OBJECT_ID == "CRTO-COMMON-HISTORY-GATE-20260830-01"
    assert config.REPRESENTATIONS == ("RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT")
    assert dict(config.BUDGETS) == {"SHORT": 128, "LONG": 2048}
    assert config.BATCH_SIZE == 64 and config.MAX_PRIMITIVE_TEAM_STEPS == 2_596_864
    assert config.FROZEN_POLICIES["evaluation_population_status"] == "FROZEN"
    assert config.FROZEN_POLICIES["audit_boundary_status"] == "FROZEN"
    before = np.random.get_state()
    seeds = {config.counter_seed(purpose, 0, 0) for purpose in config.RNG_PURPOSES}
    after = np.random.get_state()
    assert len(seeds) == len(config.RNG_PURPOSES)
    assert before[0] == after[0] and np.array_equal(before[1], after[1:][0])
    with pytest.raises(ValueError):
        config.counter_seed("gate_order", 1.2)
    with pytest.raises(ValueError):
        config.counter_seed("gate_order", "1")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="population"):
        config.RunConfig(gate_train_episodes=64).validate()
    with pytest.raises(ValueError, match="RSS"):
        config.RunConfig(peak_rss_bytes=config.PEAK_RSS_BYTES - 1).validate()


def test_source_check_cli_shape_and_run_admission_block(tmp_path: Path) -> None:
    assert source_check()["status"] == "PASS"
    parser = build_parser()
    parsed = parser.parse_args([
        "run", "--output-root", "fresh", "--result", "result.json",
        "--resource-receipt", "preflight-memory.json",
        "--run-resource-receipt", "preflight-run.json",
        "--preflight-receipt", "preflight.json",
        "--launch-resource-receipt", "launch-memory.json",
        "--launch-run-resource-receipt", "launch-run.json",
    ])
    assert parsed.action == "run"
    assert parsed.launch_resource_receipt == Path("launch-memory.json")
    assert parsed.launch_run_resource_receipt == Path("launch-run.json")
    pilot = parser.parse_args([
        "pilot", "--output-root", "pilot-root", "--result", "pilot.json",
        "--resource-receipt", "pilot-memory.json",
        "--launch-resource-receipt", "pilot-launch-memory.json",
        "--launch-run-resource-receipt", "pilot-launch-run.json",
    ])
    assert pilot.action == "pilot"
    assert pilot.output_root == Path("pilot-root")
    with pytest.raises(SystemExit):
        parser.parse_args([
            "pilot", "--output-root", "o", "--result", "r",
            "--resource-receipt", "m", "--launch-resource-receipt", "lm",
            "--launch-run-resource-receipt", "la",
            "--rng-namespace", "1",
        ])
    help_text = parser.format_help()
    assert "resume" not in help_text and "legacy-result" not in help_text
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--output-root", "fresh", "--result", "r.json", "--resume"])
    output = tmp_path / "absent-parent" / "never-created"
    result = tmp_path / "absent-parent" / "never-created.json"
    with pytest.raises(PermissionError, match="NONIDENTIFYING_MISSING_PREFLIGHT"):
        run_registered(output, result)
    assert not output.exists() and not result.exists()
    assert not output.parent.exists()


def test_source_check_rejects_legacy_import_and_generic_state_load(tmp_path: Path) -> None:
    (tmp_path / "evil.py").write_text(
        "import torch\n"
        "from experiments.candidates.commitment_residual_triggered_options.training import x\n"
        "def f(path):\n    return torch.load(path)\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="forbidden legacy module|persisted-state load"):
        source_check(tmp_path)


@pytest.mark.parametrize(
    ("filename", "source"),
    (
        ("pilot.py", "import torch\n"),
        ("production.py", "from .training import fit_fresh_predictor\n"),
        ("support_census.py", "import torch\n"),
        ("support_census_worker.py", "from .training import fit_fresh_predictor\n"),
        ("support_census.py", "from . import training\n"),
    ),
)
def test_source_check_rejects_pre_admission_torch_dependency_imports(
    tmp_path: Path, filename: str, source: str,
) -> None:
    (tmp_path / filename).write_text(source, encoding="utf-8")
    with pytest.raises(RuntimeError, match="pre-admission"):
        source_check(tmp_path)


def test_sha256_is_used_only_for_counter_addressed_rng() -> None:
    package = Path(
        "experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01"
    )
    for path in package.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name != "config.py":
            assert "hashlib" not in source and "sha256" not in source
    tree = ast.parse((package / "config.py").read_text(encoding="utf-8"))
    sha_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sha256"
    ]
    counter = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "counter_seed_for_namespace"
    )
    assert len(sha_calls) == 1 and sha_calls[0] in tuple(ast.walk(counter))


def test_model_construction_preserves_ambient_torch_rng_state() -> None:
    before = torch.random.get_rng_state().clone()
    CommonHistoryGate(config.counter_rng("gate_initialization", 0))
    FreshPredictor(config.counter_rng("predictor_initialization", 0))
    after = torch.random.get_rng_state()
    assert torch.equal(before, after)


def test_production_worker_is_one_isolated_process_with_threads_bound_before_import(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        result = Path(command[command.index("--result") + 1])
        result.write_text(json.dumps({"worker": "complete"}), encoding="utf-8")
        return subprocess.CompletedProcess(
            command, 0,
            stdout=json.dumps({"status": "PUBLISHED", "object_id": config.OBJECT_ID}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(run_module, "validate_result", lambda payload: observed.setdefault("validated", payload))
    payload = _launch_production_worker(
        output_root=tmp_path / "output",
        result_path=tmp_path / "result.json",
        preflight_receipt_path=tmp_path / "preflight.json",
        launch_resource_receipt_path=tmp_path / "launch-memory.json",
        launch_run_resource_receipt_path=tmp_path / "launch-run.json",
    )

    assert payload == {"worker": "complete"}
    command = observed["command"]
    assert command[:3] == [
        str(Path(__import__("sys").executable)), "-m",
        "experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.production_worker",
    ]
    environment = observed["kwargs"]["env"]
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        assert environment[name] == "1"
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert environment["HMASD_CRTO_PRODUCTION_WORKER"] == config.OBJECT_ID
    assert observed["validated"] == {"worker": "complete"}
    assert observed["kwargs"]["cwd"] == Path.cwd()
    assert observed["kwargs"]["check"] is False


def test_pilot_cli_launcher_binds_fixed_worker_without_importing_science(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        result = Path(command[command.index("--result") + 1])
        result.write_text('{"pilot": "complete"}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(pilot_module, "validate_pilot_result", lambda payload: observed.setdefault("validated", payload))
    payload = _launch_raw_pilot_worker(
        output_root=tmp_path / "output",
        result_path=tmp_path / "result.json",
        resource_receipt_path=tmp_path / "memory.json",
        launch_resource_receipt_path=tmp_path / "launch-memory.json",
        launch_run_resource_receipt_path=tmp_path / "launch-assess.json",
    )

    assert payload == {"pilot": "complete"}
    assert observed["command"][:3] == [
        str(Path(__import__("sys").executable)), "-m",
        "experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot",
    ]
    environment = observed["kwargs"]["env"]
    assert environment["HMASD_CRTO_PILOT_WORKER"] == config.PILOT_OBJECT_ID
    assert observed["validated"] == {"pilot": "complete"}
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        assert environment[name] == "1"
