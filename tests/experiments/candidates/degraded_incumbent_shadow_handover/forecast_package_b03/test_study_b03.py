"""B03 seed/object binding, configuration, pair publication; no learner."""

import hashlib
import json

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import study as b02
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b03 import study

B03_MASTER_HEX = "b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a"
RENEWAL_BOUNDARY = (
    "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed"
)
MODULE = "experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b03.study"


def _fake_batch(countdowns, raw_renew=None, ticks=None):
    width = len(countdowns)
    batch = study.backend.NativeBatch.__new__(study.backend.NativeBatch)
    batch.width = width
    batch.library = "no-native"
    batch._states = (study.backend._State * width)()
    batch._outputs = (study.backend._StepOutput * width)()
    if raw_renew is None:
        raw_renew = [0] * width
    if ticks is None:
        ticks = [0] * width
    for index, countdown in enumerate(countdowns):
        batch._states[index].countdown = int(countdown)
        batch._states[index].tick = int(ticks[index])
        batch._outputs[index].renew = int(raw_renew[index])
        batch._outputs[index].tick = int(ticks[index])
    return batch


def _reset_row(phase):
    names = [name for name, _ in study.backend._ResetInput._fields_ if name != "master"]
    row = {name: 0 for name in names}
    row["master"] = bytes(32)
    row["phase"] = int(phase)
    row["k_initial"] = 8
    row["k_new"] = 8
    row["reflection"] = 1
    return row


class _StubResetBatchLibrary:
    def dish_rbhr_r06_prod_reset_batch(self, reset_array, width, states, outputs):
        width = int(width)
        for index in range(width):
            states[index].countdown = reset_array[index].phase
            states[index].tick = 0
            outputs[index].renew = 0
            outputs[index].tick = 0
        return 0


def test_master_hex_is_b03_seed_73_not_b02_seed_61():
    assert study.master().hex() == B03_MASTER_HEX
    b02_hex = hashlib.sha256(f"{b02.OBJECT}/seed/61".encode("ascii")).hexdigest()
    assert study.master().hex() != b02_hex


def test_configuration_records_seed_object_flag_and_corrected_boundary():
    control = study.configuration("CONTROL")
    package = study.configuration("FORECAST_PACKAGE")
    assert control["forecast_package"] is False
    assert package["forecast_package"] is True
    for row in (control, package):
        assert row["seed"] == 73
        assert row["object"] == "DISH-FORECAST-PACKAGE-B03"
        assert row["master_hex"] == B03_MASTER_HEX
        assert row["renewal_boundary"] == RENEWAL_BOUNDARY


def test_run_arm_and_paired_result_are_b03_objects_and_publish_pair():
    assert study.run_arm.__module__ == MODULE
    assert study.paired_result.__module__ == MODULE
    control = {"status": "COMPLETE", "evaluation_rows": []}
    package = {"status": "COMPLETE", "evaluation_rows": []}
    differences = (30, -10, 0, 100)
    for index, difference in enumerate(differences):
        left = {
            "coordinate": str(index), "service_ticks": 100, "energy": 0.0,
            "hard_events": {}, "terminal": {}, "legal_transfers": 0,
        }
        control["evaluation_rows"].append(left)
        package["evaluation_rows"].append({**left, "service_ticks": 100 + difference})
    paired = study.paired_result(control, package)
    assert paired["object"] == "DISH-FORECAST-PACKAGE-B03"
    assert [row["difference"] for row in paired["paired_rows"]] == list(differences)
    assert paired["delta_package"] == 30
    assert paired["control_mean"] == 100
    assert paired["package_mean"] == 130


def test_corrected_boundary_reaches_study_native_batch_observe():
    batch = _fake_batch(countdowns=[0, 3, 0], raw_renew=[0, 1, 1])
    observation = batch.observe()
    countdown = np.array([int(batch._states[index].countdown) for index in range(batch.width)])
    np.testing.assert_array_equal(
        observation["renew"], np.asarray(countdown == 0, dtype=observation["renew"].dtype),
    )
    assert "renew_completed" in observation
    np.testing.assert_array_equal(
        observation["renew_completed"],
        np.array([0, 1, 1], dtype=observation["renew_completed"].dtype),
    )
    rows = (_reset_row(0), _reset_row(4))
    native = study.backend.native_batch_from_rows(rows, library=_StubResetBatchLibrary())
    observed = native.observe()
    native_countdown = np.array([int(native._states[index].countdown) for index in range(native.width)])
    np.testing.assert_array_equal(
        observed["renew"], np.asarray(native_countdown == 0, dtype=observed["renew"].dtype),
    )
    assert "renew_completed" in observed
    np.testing.assert_array_equal(native_countdown, np.array([0, 4]))
    np.testing.assert_array_equal(
        observed["renew"], np.array([1, 0], dtype=observed["renew"].dtype),
    )


def test_runner_publish_under_resource(tmp_path):
    pytest.importorskip("resource")
    from scripts.run_dish_forecast_package_b03 import publish
    publish(tmp_path, {"object": "DISH-FORECAST-PACKAGE-B03", "status": "INCOMPLETE",
                       "last_loss": float("nan"), "last_gradient_norm": float("inf")})
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf8"))
    assert saved["object"] == "DISH-FORECAST-PACKAGE-B03"
    assert saved["last_loss"] == "nan" and saved["last_gradient_norm"] == "inf"
