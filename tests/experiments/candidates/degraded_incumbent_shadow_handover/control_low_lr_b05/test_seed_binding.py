"""One focused plumbing/publication pass; fake learner/native, real reset and LR serialization."""
from io import BytesIO
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study as shared
from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b05 import study


def test_seed101_reaches_shared_train_eval_and_primary(monkeypatch, tmp_path):
    from scripts.run_dish_control_low_lr_b04 import main

    expected = hashlib.sha256(b"DISH-CONTROL-LOW-LR-B04/seed/101").digest()
    assert study.master() == expected
    assert shared.master() == hashlib.sha256(b"DISH-CONTROL-LOW-LR-B04/seed/89").digest()
    assert shared.configuration("CONTROL")["seed"] == 89
    assert study.configuration("CONTROL")["master_hex"] == expected.hex()
    seen = {"init": [], "reset": [], "flow": [], "policies": [], "states": [], "native": []}
    stream = BytesIO()
    torch.save({"model": {"weight": torch.tensor([1.0])},
                "optimizer": {"param_groups": [{"lr": 3e-4}, {"lr": 3e-4}]},
                "welford": {name: SimpleNamespace(count=0) for name in ("actor", "snapshot", "critic")}}, stream)
    payload = stream.getvalue()

    def initializer(**kwargs):
        seen["init"].append(kwargs)
        return payload

    factory = shared.MasterAddressedTrainResetFactory

    def reset_factory(**kwargs):
        seen["reset"].append(kwargs)
        return factory(**kwargs)

    def native(rows, **kwargs):
        result = SimpleNamespace(rows=rows, observe=lambda: None)
        seen["native"].append(result)
        return result

    def fresh(*args, **kwargs):
        state = object()
        seen["states"].append(state)
        return state

    def policy(**kwargs):
        seen["policies"].append(kwargs)
        return SimpleNamespace(model=SimpleNamespace(state_dict=lambda: {"weight": torch.tensor([1.0])}))

    class Flow:
        def __init__(self, **kwargs):
            seen["flow"].append(kwargs)
            self.trainer = SimpleNamespace(checkpoint_bytes=kwargs["checkpoint_bytes"])
        def collect_update(self, observation):
            return None
        def apply_update(self, fragments):
            return dict(optimizer_steps=32, mean_loss=1.0, mean_gradient_norm=1.0,
                        losses_finite=True, gradient_norms_finite=True)

    def evaluate(native, policy, deadline, progress, record):
        values = {"new:zero_update:raw": (90, 91, 92, 93),
                  "new:CONTROL:update16": (100, 110, 120, 130),
                  "new:LOW_LR:update16": (130, 140, 150, 160)}
        keys = [c.canonical_key() for c in shared.coordinates()]
        record["service_ticks"] = values[record["source"]][keys.index(record["coordinate"])]

    monkeypatch.setattr(shared, "load_host", lambda host: None)
    monkeypatch.setattr(shared, "build_master_addressed_initial_state", initializer)
    monkeypatch.setattr(shared, "MasterAddressedTrainResetFactory", reset_factory)
    monkeypatch.setattr(shared.backend, "native_batch_from_rows", native)
    monkeypatch.setattr(shared, "RecurrentRolloutState", SimpleNamespace(fresh=fresh))
    monkeypatch.setattr(shared, "BatchedRecurrentPolicy", policy)
    monkeypatch.setattr(shared, "TrainingMeasurements", lambda native, *args: native)
    monkeypatch.setattr(shared, "NativePersistentTrainingFlow", Flow)
    monkeypatch.setattr(shared, "evaluate_episode", evaluate)
    # Real movement helper reads only the model mapping in these synthetic bytes.
    for mode, arm in (("shared", None), ("run", "CONTROL"), ("run", "LOW_LR")):
        output = tmp_path / (arm or "shared")
        argv = ["b05", mode, "--seed", "101", "--out", str(output),
                "--admission", str(tmp_path / "synthetic-admission.json")]
        if arm:
            argv += ["--arm", arm, "--shared", str(tmp_path / "shared"),
                     "--shared-preparation-seconds", "1"]
        if arm == "LOW_LR":
            argv += ["--control-summary", str(tmp_path / "CONTROL" / "summary.json")]
        monkeypatch.setattr(sys, "argv", argv)
        assert main(seed=study.SEED, object_name=study.OBJECT) == 0
        saved = json.loads((output / "summary.json").read_text())
        assert (saved["seed"], saved["object"], saved["master_hex"]) == (101, study.OBJECT, expected.hex())
        if arm:
            assert len(saved["curves"]) == 16
            assert all(row["learning_rates"] == [shared.LEARNING_RATES[arm]] * 2 for row in saved["curves"])
    assert seen["init"] == [dict(master=expected, block=0, arm="STRUCTURED")]
    assert seen["reset"] == [dict(master=expected, block=0, arm="STRUCTURED")] * 2
    assert [flow["master"] for flow in seen["flow"]] == [expected, expected]
    assert seen["flow"][0]["native"] is not seen["flow"][1]["native"]
    assert all(flow["forecast_package"] is False for flow in seen["flow"])
    for flow in seen["flow"]:
        loaded = torch.load(BytesIO(flow["checkpoint_bytes"]), weights_only=False)
        assert loaded["model"]["weight"].tolist() == [1.0]
        assert all(state.count == 0 for state in loaded["welford"].values())
    assert [p["checkpoint_bytes"] for p in seen["policies"][:4]] == [payload] * 4
    assert len(seen["states"]) == len({id(s) for s in seen["states"]}) == 12
    resets = json.loads((tmp_path / "shared" / "resets.json").read_text())
    assert resets == shared.recorded_resets(expected)
    assert resets != shared.recorded_resets(shared.master())
    eval_native = [n for n in seen["native"] if len(n.rows) == 1]
    assert [n.rows[0] for n in eval_native] == list(resets.values()) * 3
    train_native = [n for n in seen["native"] if len(n.rows) == 32]
    expected_train = factory(master=expected, block=0, arm="STRUCTURED").rows(np.zeros(32, dtype=np.int64))
    assert all(n.rows == expected_train for n in train_native)
    paired = json.loads((tmp_path / "LOW_LR" / "paired.json").read_text())
    assert (paired["object"], paired["seed"]) == (study.OBJECT, 101)
    assert [paired[k] for k in ("reference_mean", "control_mean", "low_lr_mean")] == [91.5, 115, 145]
    assert [paired[k] for k in ("delta_lr", "d_control_new", "d_low_lr_new")] == [30, 23.5, 53.5]
    assert [r["low_lr_minus_control"] for r in paired["rows"]] == [30] * 4
    assert shared.OBJECT == "DISH-CONTROL-LOW-LR-B04" and shared.SEED == 89
