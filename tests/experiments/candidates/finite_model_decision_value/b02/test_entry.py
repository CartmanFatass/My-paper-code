import pytest

from experiments.candidates.finite_model_decision_value.b02 import study
from scripts import hmasd_admission, run_fmdv_b02


def test_entry_requires_admission_before_science_and_binds_frozen_plan(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(study, "run_study", lambda *args: calls.append(args))

    def reject(*args, **kwargs):
        raise RuntimeError("missing admission fixture")

    monkeypatch.setattr(hmasd_admission, "require_admission", reject)
    out = tmp_path / "uncreated"
    argv = ["--out", str(out), "--launch-sha", "f" * 40]
    with pytest.raises(RuntimeError, match="missing admission"):
        run_fmdv_b02.main(argv)
    assert not calls and not out.exists()
    with pytest.raises(SystemExit):
        run_fmdv_b02.main(argv + ["--seed", "441831"])
    with pytest.raises(SystemExit):
        run_fmdv_b02.main(argv + ["--model-seed", "442073"])
    assert not calls and not out.exists()
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "f" * 40})
    with pytest.raises(ValueError, match="disagrees"):
        run_fmdv_b02.main(["--out", str(out), "--launch-sha", "e" * 40])
    assert not calls
    run_fmdv_b02.main(argv)
    assert calls == [(out, "f" * 40, study.Config())]
    config = calls[0][2]
    assert (config.seed, config.model_seed) == (925831, 926073)
    assert (config.contexts, config.horizon, config.batch) == (256, 96, 16)
    assert (config.calibration_phase, config.evaluation_phase, config.model_phase) == (50, 51, 52)
    assert (config.calibration_steps, config.particles_low, config.particles_high) == (4, 32, 256)
