"""Only the new CLI binding; no learner import, scientific RNG or model."""
import importlib.util
from pathlib import Path
import sys
import types

import pytest

from experiments.candidates.acvc.training_use_b02.protocol import (
    CAPS, CARD, EVALUATION_NAMESPACE, MASTER, OBJECT,
)


@pytest.mark.parametrize("arm", ["C", "F"])
def test_new_pair_reaches_unchanged_runner_with_exact_identity(monkeypatch, arm):
    calls = []
    fake = types.ModuleType("run_acvc_fresh_dense_reuse_b01")
    fake.run = lambda *args, **kwargs: calls.append((args, kwargs)) or 0
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_training_use_b02.py"
    spec = importlib.util.spec_from_file_location("new_training_use_binding", script)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(sys, "argv", [str(script), "--arm", arm, "--output", "fixture-unused",
                                    "--launch-sha", "fixed", "--execution-seconds", "260"])
    assert runner.main() == 0
    args, options = calls[0]
    assert args[0] == Path("fixture-unused") and args[1] == "fixed" and args[3] == 260
    assert options == dict(master=20319, evaluation_namespace=30319, object_name=OBJECT,
                          card_path=CARD, allocation_seconds=CAPS, train_rule=arm, eval_arms=("F",))
    assert CAPS == dict(whole_supervised_arm=270, native_sum=540, future_support=300, future_complete=840)
    assert (MASTER, EVALUATION_NAMESPACE) == (20319, 30319)
    assert not Path("fixture-unused").exists()
    monkeypatch.setattr(sys, "argv", sys.argv + ["--seed", "20261"])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2 and len(calls) == 1
