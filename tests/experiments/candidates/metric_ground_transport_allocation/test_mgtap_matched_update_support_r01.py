from __future__ import annotations

import inspect
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from experiments.candidates.metric_ground_transport_allocation import artifacts, config, rng, run
from experiments.candidates.metric_ground_transport_allocation import analysis as result_analysis


OWNED_FIXTURE_ROOT = Path(
    "temp/directions/metric_ground_transport_allocation/test/"
    "matched-update-support-r01-construction/pytest-fixtures"
)


@pytest.fixture
def owned_fixture(request: pytest.FixtureRequest) -> Path:
    root = OWNED_FIXTURE_ROOT / request.node.name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    if root.exists():
        shutil.rmtree(root)
    if OWNED_FIXTURE_ROOT.exists() and not any(OWNED_FIXTURE_ROOT.iterdir()):
        OWNED_FIXTURE_ROOT.rmdir()


def _calibration_fixture() -> np.ndarray:
    values = np.zeros(
        (4, len(config.GRID), len(config.CALIBRATION_SEEDS), 2),
        dtype=np.float64,
    )
    values[:, :, :, 0] = 0.0
    values[:, :, :, 1] = config.STATIONARITY_TOLERANCE
    return values


def _write_manifest(root: Path, *, gate_passed: bool) -> None:
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "revision": config.REVISION,
                "stochastic_namespace": config.STOCHASTIC_NAMESPACE,
                "gate_passed": gate_passed,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    np.savez(root / "tables.npz", fixture=np.asarray([0], dtype=np.int8))


def _write_gate_summary(root: Path) -> None:
    (root / "summary.json").write_text(
        json.dumps(
            {
                "revision": config.REVISION,
                "stochastic_namespace": config.STOCHASTIC_NAMESPACE,
                "branch": "BOUNDED_NONIDENTIFICATION_STRUCTURAL",
                "gate_failure_reason": "ALL_CELL_STATIONARITY_GATE_FALSE",
                "resources": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_all_pass_files(root: Path) -> None:
    _write_manifest(root, gate_passed=True)
    (root / "summary.json").write_text(
        json.dumps(
            {
                "revision": config.REVISION,
                "stochastic_namespace": config.STOCHASTIC_NAMESPACE,
                "analysis_status": "PENDING_COMPLETE_TREE_VALIDATION",
                "resources": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    for seed in config.FINAL_SEEDS:
        (root / f"seed_{seed}.npz").write_bytes(b"non-scientific fixture")


def test_01_literal_revision_namespace_horizons_and_tolerance() -> None:
    assert config.REVISION == "MGTAP-B1-MATCHED-UPDATE-SUPPORT-20260827-R01"
    assert config.STOCHASTIC_NAMESPACE == "mgtap_b1_matched_update_support_20260827_r01"
    assert config.CALIBRATION_UPDATES == 256
    assert config.CHECKPOINTS == (224, 256)
    assert config.FINAL_UPDATES == config.CONCLUSION_CHECKPOINT == 512
    assert config.STATIONARITY_TOLERANCE == 0.005


def test_02_literal_seed_families_are_disjoint_from_revision_04() -> None:
    revision_04 = {
        1103, 1129, 1151, 1171,
        2003, 2027, 2053, 2081, 2111, 2141, 2179, 2203,
        2237, 2269, 2297, 2333, 2357, 2389, 2417, 2447,
    }
    assert config.CALIBRATION_SEEDS == (3109, 3119, 3121, 3137)
    assert config.FINAL_SEEDS == (
        4001, 4003, 4007, 4013, 4019, 4021, 4027, 4049,
        4051, 4057, 4073, 4079, 4091, 4093, 4099, 4111,
    )
    assert set(config.CALIBRATION_SEEDS).isdisjoint(config.FINAL_SEEDS)
    assert (set(config.CALIBRATION_SEEDS) | set(config.FINAL_SEEDS)).isdisjoint(
        revision_04
    )


def test_03_registered_address_payload_begins_with_r01_namespace() -> None:
    payload = json.loads(rng._address_payload(("fixture", 17, 3)))
    assert payload == [config.STOCHASTIC_NAMESPACE, "fixture", 17, 3]
    assert "MGTAP-B1-SCIENCE-20260813-04" not in rng._address_payload(("fixture",)).decode()


def test_04_conditional_workload_counts_are_exact() -> None:
    assert config.GATE_ONLY_COUNTS == {
        "calibration_training_decisions": 2_359_296,
        "validation_decisions": 294_912,
        "conclusion_training_decisions": 0,
        "base_evaluation_decisions": 0,
        "replay_evaluation_decisions": 0,
        "autoregressive_agent_steps": 15_925_248,
        "optimizer_updates": 24_576,
    }
    assert config.workload_counts() == config.EXPECTED_COUNTS
    assert config.EXPECTED_COUNTS["optimizer_updates"] == 57_344
    assert config.EXPECTED_COUNTS["autoregressive_agent_steps"] == 46_596_096


def test_05_selection_uses_v256_with_frozen_tie_break() -> None:
    selected = run._select_calibration(_calibration_fixture())
    # Every grid score ties. Smaller learning rate wins, then larger lambda.
    assert np.array_equal(selected["selected_grid_index"], np.asarray([1, 1, 1, 1]))


def test_06_gate_is_inclusive_and_applies_to_every_cell() -> None:
    selected = run._select_calibration(_calibration_fixture())
    assert selected["gate_passed"] is True
    assert np.array_equal(selected["gate_vector"], np.ones(4, dtype=bool))
    values = _calibration_fixture()
    values[3, :, :, 1] = np.nextafter(config.STATIONARITY_TOLERANCE, np.inf)
    assert run._select_calibration(values)["gate_passed"] is False


def test_07_missing_incomplete_or_nonfinite_calibration_fails_closed() -> None:
    incomplete = np.zeros((3, len(config.GRID), len(config.CALIBRATION_SEEDS), 2))
    assert run._select_calibration(incomplete)["gate_passed"] is False
    nonfinite = _calibration_fixture()
    nonfinite[0, 0, 0, 0] = np.nan
    result = run._select_calibration(nonfinite)
    assert result["complete"] is False
    assert result["gate_passed"] is False


def test_08_gate_failure_returns_before_any_final_activity() -> None:
    source = inspect.getsource(run.production)
    gate_start = source.index("if not gate_passed:")
    gate_return = source.index("        return", gate_start)
    final_loop = source.index("for seed in FINAL_SEEDS:")
    assert gate_start < gate_return < final_loop
    gate_block = source[gate_start:gate_return]
    for forbidden in ("conclusion_fit(", "evaluate_fit(", "analyze("):
        assert forbidden not in gate_block


def test_09_gate_terminal_tree_has_exact_three_files(owned_fixture: Path) -> None:
    _write_manifest(owned_fixture, gate_passed=False)
    _write_gate_summary(owned_fixture)
    artifacts.validate_tree(owned_fixture, gate_passed=False)
    (owned_fixture / "seed_4001.npz").write_bytes(b"forbidden")
    with pytest.raises(RuntimeError, match="artifact file set mismatch"):
        artifacts.validate_tree(owned_fixture, gate_passed=False)


def test_10_gate_summary_enforces_evidence_firewall(owned_fixture: Path) -> None:
    _write_manifest(owned_fixture, gate_passed=False)
    _write_gate_summary(owned_fixture)
    summary_path = owned_fixture / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["primary_relation"] = "forbidden"
    summary_path.write_text(json.dumps(summary) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="evidence firewall"):
        artifacts.validate_tree(owned_fixture, gate_passed=False)


def test_11_all_pass_tree_has_sixteen_literal_packets(owned_fixture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_all_pass_files(owned_fixture)
    seen: list[int] = []
    monkeypatch.setattr(artifacts, "validate_seed_packet", lambda _path, seed: seen.append(seed))
    artifacts.validate_tree(owned_fixture, gate_passed=True, preanalysis=True)
    assert seen == list(config.FINAL_SEEDS)
    assert len({path.name for path in owned_fixture.iterdir()}) == 19


def test_12_seed_packet_binds_r01_identity(owned_fixture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = 49_152
    path = owned_fixture / "seed_4001.npz"
    minimal_existing = {
        "N", "arm", "binding", "feasibility_residuals",
        "replay_feasibility_residuals", "reward", "replay_reward",
        "normalized_endpoint", "replay_normalized_endpoint",
        "checkpoint_parameters", "selected_hyperparameters",
    }
    monkeypatch.setattr(artifacts, "REQUIRED_SEED_FIELDS", minimal_existing)
    roster = np.resize(np.asarray([4, 6, 8, 12], dtype=np.int8), rows)
    arm = np.resize(np.asarray([0, 1], dtype=np.int8), rows)
    binding = np.resize(np.asarray([0, 1], dtype=np.int8), rows)
    zeros = np.zeros(rows, dtype=np.float64)
    np.savez_compressed(
        path,
        N=roster,
        arm=arm,
        binding=binding,
        feasibility_residuals=np.zeros((rows, 1), dtype=np.int8),
        replay_feasibility_residuals=np.zeros((rows, 1), dtype=np.int8),
        reward=zeros,
        replay_reward=zeros.copy(),
        normalized_endpoint=zeros.copy(),
        replay_normalized_endpoint=zeros.copy(),
        checkpoint_parameters=np.zeros((4, 60), dtype=np.float64),
        selected_hyperparameters=np.zeros((4, 2), dtype=np.float64),
        revision=np.asarray(config.REVISION),
        stochastic_namespace=np.asarray(config.STOCHASTIC_NAMESPACE),
        conclusion_checkpoint=np.asarray(512, dtype=np.int16),
        packet_seed=np.asarray(4001, dtype=np.int32),
        selected_grid_index=np.zeros(4, dtype=np.int8),
    )
    artifacts.validate_seed_packet(path, 4001)
    with pytest.raises(RuntimeError, match="identity mismatch"):
        artifacts.validate_seed_packet(path, 4003)


def test_13_partial_or_extra_all_pass_tree_rejects_before_analysis(owned_fixture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_all_pass_files(owned_fixture)
    monkeypatch.setattr(artifacts, "validate_seed_packet", lambda _path, _seed: None)
    (owned_fixture / "seed_4111.npz").unlink()
    with pytest.raises(RuntimeError, match="artifact file set mismatch"):
        artifacts.validate_tree(owned_fixture, gate_passed=True, preanalysis=True)
    (owned_fixture / "seed_4111.npz").write_bytes(b"non-scientific fixture")
    (owned_fixture / "extra.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="artifact file set mismatch"):
        artifacts.validate_tree(owned_fixture, gate_passed=True, preanalysis=True)


def test_14_complete_preanalysis_validation_precedes_analysis() -> None:
    source = inspect.getsource(run.production)
    final_loop = source.index("for seed in FINAL_SEEDS:")
    prevalidation = source.index(
        "validate_tree(temp, gate_passed=True, preanalysis=True)", final_loop
    )
    analysis_call = source.index("analysis = analyze(", prevalidation)
    terminal_validation = source.index(
        "validate_tree(temp, gate_passed=True)", analysis_call
    )
    install_call = source.index("install(temp, output, gate_passed=True", terminal_validation)
    assert final_loop < prevalidation < analysis_call < terminal_validation < install_call


def test_15_activity_marker_precedes_first_registered_generator() -> None:
    trainer_path = Path(
        "experiments/candidates/metric_ground_transport_allocation/trainer.py"
    )
    source = trainer_path.read_text(encoding="utf-8")
    group = source[source.index("def _training_group"):source.index("def _decode_group")]
    assert group.index("_mark_registered_activity()") < group.index("generator(")
    assert '"revision": REVISION' in source
    assert '"stochastic_namespace": STOCHASTIC_NAMESPACE' in source


def test_16_free_intact_cut_identity_remains_fail_closed() -> None:
    packet: dict[str, np.ndarray] = {
        "checkpoint_parameters": np.zeros((4, 60), dtype=np.float64),
        "arm": np.asarray([0, 0, 1, 1], dtype=np.int8),
        "binding": np.asarray([0, 1, 0, 1], dtype=np.int8),
    }
    for key in (
        "sampled_step_actions", "coupling_X", "idle_iota", "unmet_mu",
        "reward", "normalized_endpoint",
    ):
        packet[key] = np.zeros((4, 1), dtype=np.float64)
    run._free_identity(packet)
    packet["reward"][3, 0] = 1.0
    with pytest.raises(RuntimeError, match="FREE intact/cut output leakage"):
        run._free_identity(packet)


def test_17_first_true_result_map_order_is_unchanged() -> None:
    source = inspect.getsource(result_analysis.analyze)
    ordered = [
        'branch = "BOUNDED_NONIDENTIFICATION_STRUCTURAL"',
        'branch = "RETAIN_METRIC_FINITE_BUDGET"',
        'branch = "DELETE_METRIC_EQUAL_CLASS"',
        'branch = "GENERIC_FINITE_BUDGET_EFFECT"',
        'branch = "SIZE_INTERACTION"',
        'branch = "BOUNDED_NONIDENTIFICATION"',
    ]
    positions = [source.index(item) for item in ordered]
    assert positions == sorted(positions)


def test_18_caps_cli_preexistence_and_atomic_install(owned_fixture: Path) -> None:
    assert run.WALL_CAP_SECONDS == 28_800
    assert run.CPU_CAP_SECONDS == 115_200
    assert run.RSS_CAP_BYTES == 4 * 1024**3
    assert run.DISK_CAP_BYTES == 8 * 1024**3
    source = inspect.getsource(run.main)
    assert 'parser.add_argument("--output", type=Path)' in source
    assert 'parser.add_argument("--certificate", action="store_true")' in source
    assert '"revision": REVISION' in source
    assert '"stochastic_namespace": STOCHASTIC_NAMESPACE' in source

    final = owned_fixture / "installed"
    temporary = artifacts.create_temp_root(final)
    _write_manifest(temporary, gate_passed=False)
    _write_gate_summary(temporary)
    artifacts.install(temporary, final, gate_passed=False)
    assert final.is_dir() and not temporary.exists()
    with pytest.raises(FileExistsError):
        artifacts.create_temp_root(final)
