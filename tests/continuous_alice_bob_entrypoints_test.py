"""Proof-sized import checks for the relocated Alice/Bob entrypoints."""

import importlib
import importlib.util
from pathlib import Path


def test_continuous_alice_bob_entrypoints_resolve_from_package():
    config = importlib.import_module(
        "experiments.continuous_alice_bob.config_continuous_alice_bob"
    )
    train_spec = importlib.util.find_spec(
        "experiments.continuous_alice_bob.train_continuous_alice_bob"
    )
    evaluate_spec = importlib.util.find_spec(
        "experiments.continuous_alice_bob.evaluate_continuous_alice_bob"
    )

    assert config.Config.n_agents == 2
    assert train_spec is not None and train_spec.origin is not None
    assert evaluate_spec is not None and evaluate_spec.origin is not None
    assert Path(train_spec.origin).is_file()
    assert Path(evaluate_spec.origin).is_file()
    train_source = Path(train_spec.origin).read_text(encoding="utf-8")
    evaluate_source = Path(evaluate_spec.origin).read_text(encoding="utf-8")
    expected_import = (
        "from experiments.continuous_alice_bob.config_continuous_alice_bob import Config"
    )
    assert expected_import in train_source
    assert expected_import in evaluate_source
    compile(train_source, train_spec.origin, "exec")
    compile(evaluate_source, evaluate_spec.origin, "exec")

    repo_root = Path(__file__).resolve().parents[1]
    for predecessor in (
        "config_continuous_alice_bob.py",
        "train_continuous_alice_bob.py",
        "evaluate_continuous_alice_bob.py",
        "config_1_optimized.py",
        "run_experiment_parallel_configs.py",
    ):
        assert not (repo_root / predecessor).exists()
