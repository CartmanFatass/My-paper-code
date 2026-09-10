"""Pure-data and stub coverage of the new fixed object/master binding."""
import importlib.util
from pathlib import Path

import pytest
import torch

from experiments.candidates.vsp_c1.native_hold_value_b01 import study

OBJECT = "VSPC1-NATIVE-HOLD-VALUE-B10"
CARD = "docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B10_SCIENCE_CARD_20260909.md"


def load_cli():
    path = Path(__file__).resolve().parents[5] / "scripts/run_vspc1_native_hold_value_b10.py"
    spec = importlib.util.spec_from_file_location("vspc1_b10_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("status,code", [("COMPLETE", 0), ("PRIMARY_COMPLETE_WITH_LIMITS", 0), ("INCOMPLETE", 1)])
def test_fixed_cli_binding_and_exit(monkeypatch, tmp_path, status, code):
    cli = load_cli()
    threads, calls = [], []
    monkeypatch.setattr(torch, "set_num_threads", lambda n: threads.append(n))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: threads.append(n))

    def run(config, out, start, **identity):
        calls.append((config, out, start, identity))
        return dict(mode="BINDING_STUB", status=status)

    monkeypatch.setattr(study, "run_pair", run)
    assert cli.main(["--seed", "8501", "--out", str(tmp_path)]) == code
    assert threads == [1, 1]
    assert calls == [(study.Config(seed=8501, train_episodes=768), tmp_path, cli.WHOLE_START,
                      dict(object_id=OBJECT, card=CARD, normalize_value=True,
                           second_mlp_width=133, extra_init_seed=850100012, fixed_endpoints=True))]


@pytest.mark.parametrize("args", [["--seed", "8401"], ["--seed", "8403"], ["--seed", "9001"],
                                  ["--seed", "8501", "--engineering-fixture"],
                                  ["--seed", "8501", "--width", "133"],
                                  ["--seed", "8501", "--normalize-value"],
                                  ["--seed", "8501", "--train-episodes", "512"]])
def test_invalid_binding_rejected_before_scientific_state(monkeypatch, tmp_path, args):
    cli = load_cli()

    def forbidden(*args, **kwargs):
        pytest.fail("invalid binding reached scientific state boundary")

    monkeypatch.setattr(torch, "set_num_threads", forbidden)
    monkeypatch.setattr(study, "run_pair", forbidden)
    with pytest.raises(SystemExit) as error:
        cli.main(args + ["--out", str(tmp_path)])
    assert error.value.code == 2


@pytest.mark.parametrize("arm,count,architecture", [
    ("GATED-V", 34817, "136->128->128->1 + 128x5 hold gate"),
    ("MLP-V", 34827, "136->128->133->1")])
def test_generic_checkpoint_identity(arm, count, architecture):
    identity = study.checkpoint_identity(study.Config(seed=8501, train_episodes=768), arm, "bound-source", OBJECT,
                                         True, second_mlp_width=133, extra_init_seed=850100012)
    assert identity == dict(object=OBJECT, algorithm=arm, arm=arm, seed=8501,
                           mode="UAV_B_EXPLORE", ratio_grouping="agent_compound",
                           launch_sha="bound-source", critic_architecture=architecture,
                           critic_parameter_count=count,
                           configuration=dict(seed=8501, fixture=False, horizon=256,
                                              train_episodes=768, eval_episodes=32, chunk=32,
                                              arm_cap=1800, pair_cap=3600,
                                              ratio_grouping="agent_compound",
                                              value_normalization="cumulative_population_fp32",
                                              entropy_coef=.01, second_mlp_width=133,
                                              extra_initialization_seed=850100012))
