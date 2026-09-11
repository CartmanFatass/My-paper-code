"""B04 seed/rate/reset/pair checks; no learner run, no native host, no development panel."""

from io import BytesIO
import hashlib
import json
import time

import pytest
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    EvaluationCoordinate, _reset_row, parameter_movement,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    build_master_addressed_initial_state,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    run_full_4096_dry_update,
)

B04_MASTER_HEX = "665c8d879ef9d289d4ad6d4d3bf051643d9f17bb05c97521566dc48a77071c9d"
B03_MASTER_HEX = "b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a"


@pytest.fixture(scope="module")
def payload():
    torch.set_num_threads(1)
    return build_master_addressed_initial_state(master=study.master(), block=0, arm="STRUCTURED")


def test_master_hex_is_b04_seed_89_not_b03_seed_73():
    assert study.master().hex() == B04_MASTER_HEX
    b03_hex = hashlib.sha256(b"DISH-FORECAST-PACKAGE-B03/seed/73").hexdigest()
    assert b03_hex == B03_MASTER_HEX
    assert study.master().hex() != b03_hex


def test_set_learning_rate_rewrites_both_groups(payload):
    original = torch.load(BytesIO(payload), map_location="cpu", weights_only=False)
    rewritten = study.set_learning_rate(payload, 3e-5)
    loaded = torch.load(BytesIO(rewritten), map_location="cpu", weights_only=False)
    assert len(loaded["optimizer"]["param_groups"]) == 2
    assert study.learning_rates(rewritten) == [3e-5, 3e-5]
    assert study.learning_rates(study.set_learning_rate(payload, 3e-4)) == [3e-4, 3e-4]
    assert study.learning_rates(payload) == [3e-4, 3e-4]
    for before, after in zip(original["optimizer"]["param_groups"], loaded["optimizer"]["param_groups"]):
        assert after["lr"] == 3e-5
        assert after["betas"] == before["betas"]
        assert after["eps"] == before["eps"]
        assert after["weight_decay"] == before["weight_decay"]
    for name, tensor in original["model"].items():
        torch.testing.assert_close(tensor, loaded["model"][name], rtol=0, atol=0)
        assert tensor.detach().contiguous().cpu().numpy().tobytes() == (
            loaded["model"][name].detach().contiguous().cpu().numpy().tobytes())
    counts = {}
    for name in ("actor", "snapshot", "critic"):
        left, right = original["welford"][name], loaded["welford"][name]
        assert left.count == right.count == 0
        assert left.mean.detach().contiguous().cpu().numpy().tobytes() == (
            right.mean.detach().contiguous().cpu().numpy().tobytes())
        assert left.m2.detach().contiguous().cpu().numpy().tobytes() == (
            right.m2.detach().contiguous().cpu().numpy().tobytes())
        counts[name] = int(left.count)
    print("B04 initializer_model_norm", study.model_norm(original["model"]))
    print("B04 welford_counts", counts)
    print("B04 rates_constructed", study.learning_rates(payload))
    print("B04 rates_low_lr", study.learning_rates(rewritten))


def test_chained_engine_updates_carry_the_rate(payload):
    low_payload = study.set_learning_rate(payload, 3e-5)
    control_payload = study.set_learning_rate(payload, 3e-4)
    started = time.perf_counter()
    low_first = run_full_4096_dry_update(arm="STRUCTURED", resume_checkpoint_bytes=low_payload,
                                         forecast_package=False)
    low_second = run_full_4096_dry_update(arm="STRUCTURED",
                                          resume_checkpoint_bytes=low_first["private_checkpoint_bytes"],
                                          forecast_package=False)
    control_first = run_full_4096_dry_update(arm="STRUCTURED", resume_checkpoint_bytes=control_payload,
                                             forecast_package=False)
    control_second = run_full_4096_dry_update(
        arm="STRUCTURED", resume_checkpoint_bytes=control_first["private_checkpoint_bytes"],
        forecast_package=False)
    wall = time.perf_counter() - started
    print("B04 chained_update_wall_seconds", wall)
    print("B04 chained_update_walls",
          [low_first["wall_seconds"], low_second["wall_seconds"],
           control_first["wall_seconds"], control_second["wall_seconds"]])
    assert study.learning_rates(low_first["private_checkpoint_bytes"]) == [3e-5, 3e-5]
    assert study.learning_rates(low_second["private_checkpoint_bytes"]) == [3e-5, 3e-5]
    assert study.learning_rates(control_first["private_checkpoint_bytes"]) == [3e-4, 3e-4]
    assert study.learning_rates(control_second["private_checkpoint_bytes"]) == [3e-4, 3e-4]
    assert low_second["update"] == 2
    assert control_second["update"] == 2
    low_move = parameter_movement(low_payload, low_first["private_checkpoint_bytes"])["l2_displacement"]
    control_move = parameter_movement(control_payload, control_first["private_checkpoint_bytes"])["l2_displacement"]
    print("B04 one_update_l2_displacement", {"LOW_LR": low_move, "CONTROL": control_move})
    assert low_move < control_move


def test_configuration_differs_only_in_arm_and_learning_rate(payload):
    control = study.configuration("CONTROL")
    low_lr = study.configuration("LOW_LR")
    assert control["forecast_package"] is False and low_lr["forecast_package"] is False
    differing = {key for key in control if control[key] != low_lr[key]}
    assert differing == {"arm", "learning_rate"}
    assert set(control) == set(low_lr)
    for arm, row in (("CONTROL", control), ("LOW_LR", low_lr)):
        baked = study.set_learning_rate(payload, study.LEARNING_RATES[arm])
        assert row["learning_rate"] == study.learning_rates(baked)[0]
        assert row["arm"] == arm
        assert row["object"] == "DISH-CONTROL-LOW-LR-B04"
        assert row["seed"] == 89


def test_recorded_resets_json_round_trip():
    resets = study.recorded_resets(study.master())
    keys = list(resets)
    expected = [coordinate.canonical_key() for coordinate in study.coordinates()]
    assert keys == expected
    assert len(keys) == 4
    loaded = json.loads(json.dumps(resets))
    assert list(loaded) == expected
    for coordinate in study.coordinates():
        key = coordinate.canonical_key()
        assert loaded[key] == dict(_reset_row(study.master(), coordinate))
        assert coordinate.speed_stratum == "SPEED_4"
        assert isinstance(coordinate, EvaluationCoordinate)


def test_paired_result_on_handwritten_summaries():
    keys = [coordinate.canonical_key() for coordinate in study.coordinates()]
    reference_services = (90, 91, 92, 93)
    control_services = (100, 110, 120, 130)
    low_services = (130, 140, 150, 160)

    def rows(values, source):
        return [{
            "coordinate": key, "service_ticks": value, "source": source,
        } for key, value in zip(keys, values)]

    control = {"status": "COMPLETE", "evaluation_rows": rows(control_services, "new:CONTROL:update16")}
    low_lr = {"status": "COMPLETE", "evaluation_rows": rows(low_services, "new:LOW_LR:update16")}
    reference = {"status": "COMPLETE", "reference_rows": rows(reference_services, "new:zero_update:raw")}
    paired = study.paired_result(control, low_lr, reference)
    assert paired["object"] == "DISH-CONTROL-LOW-LR-B04"
    assert paired["seed"] == 89
    assert paired["scale_ticks"] == 24
    assert paired["reference_mean"] == sum(reference_services) / 4
    assert paired["control_mean"] == sum(control_services) / 4
    assert paired["low_lr_mean"] == sum(low_services) / 4
    assert paired["delta_lr"] == 30
    assert paired["d_control_new"] == 23.5
    assert paired["d_low_lr_new"] == 53.5
    assert [row["reference_source"] for row in paired["rows"]] == ["new:zero_update:raw"] * 4
    assert [row["control_source"] for row in paired["rows"]] == ["new:CONTROL:update16"] * 4
    assert [row["low_lr_source"] for row in paired["rows"]] == ["new:LOW_LR:update16"] * 4
    assert [row["low_lr_minus_control"] for row in paired["rows"]] == [30, 30, 30, 30]
    missing = {"status": "COMPLETE", "evaluation_rows": control["evaluation_rows"][:3]}
    with pytest.raises(ValueError, match="coordinate"):
        study.paired_result(missing, low_lr, reference)
    with pytest.raises(ValueError, match="COMPLETE"):
        study.paired_result({"status": "INCOMPLETE", "evaluation_rows": control["evaluation_rows"]},
                            low_lr, reference)


def test_runner_publish_under_resource(tmp_path):
    pytest.importorskip("resource")
    from scripts.run_dish_control_low_lr_b04 import publish
    publish(tmp_path, {"object": "DISH-CONTROL-LOW-LR-B04", "status": "INCOMPLETE",
                       "last_loss": float("nan"), "last_gradient_norm": float("inf")})
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf8"))
    assert saved["object"] == "DISH-CONTROL-LOW-LR-B04"
    assert saved["last_loss"] == "nan" and saved["last_gradient_norm"] == "inf"
