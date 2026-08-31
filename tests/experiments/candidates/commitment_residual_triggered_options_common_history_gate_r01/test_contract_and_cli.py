from pathlib import Path
import ast

import numpy as np
import pytest
import torch

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import config
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    build_parser, run_registered, source_check,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.models import (
    CommonHistoryGate, FreshPredictor,
)


def test_contract_constants_rng_domains_and_ambient_state() -> None:
    assert config.OBJECT_ID == "CRTO-COMMON-HISTORY-GATE-20260830-01"
    assert config.REPRESENTATIONS == ("RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT")
    assert dict(config.BUDGETS) == {"SHORT": 128, "LONG": 2048}
    assert config.BATCH_SIZE == 64 and config.MAX_PRIMITIVE_TEAM_STEPS == 2_596_864
    assert config.INHERITED_ASSUMPTIONS["evaluation_population_status"] == "INHERITED_ASSUMPTION"
    assert config.INHERITED_ASSUMPTIONS["audit_boundary_status"] == "INHERITED_ASSUMPTION"
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
    parsed = parser.parse_args(["run", "--output-root", "fresh", "--result", "result.json"])
    assert parsed.action == "run"
    help_text = parser.format_help()
    assert "resume" not in help_text and "legacy-result" not in help_text
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--output-root", "fresh", "--result", "r.json", "--resume"])
    output = tmp_path / "absent-parent" / "never-created"
    result = tmp_path / "absent-parent" / "never-created.json"
    with pytest.raises(PermissionError, match="INHERITED_ASSUMPTIONS"):
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
    counter = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "counter_seed")
    assert len(sha_calls) == 1 and sha_calls[0] in tuple(ast.walk(counter))


def test_model_construction_preserves_ambient_torch_rng_state() -> None:
    before = torch.random.get_rng_state().clone()
    CommonHistoryGate(config.counter_rng("gate_initialization", 0))
    FreshPredictor(config.counter_rng("predictor_initialization", 0))
    after = torch.random.get_rng_state()
    assert torch.equal(before, after)
