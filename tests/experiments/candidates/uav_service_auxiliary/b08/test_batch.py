"""Batch outcome blindness and common-initial admission using fast fixtures."""

from types import SimpleNamespace
import json

import pytest

from experiments.candidates.uav_service_auxiliary.b08 import native, training


@pytest.mark.parametrize("failure", (None, "N", "initialization"))
def test_fixed_batch_panel_count_order_and_no_automatic_retry(tmp_path, monkeypatch, failure):
    calls = []
    initialized = 0
    monkeypatch.setattr(native.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(native.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(native, "make_b08_config", lambda spec: SimpleNamespace())
    monkeypatch.setattr(native, "fixed_config_record", lambda spec, config: {"test_fixture": True})

    def new_agent(*args, **kwargs):
        nonlocal initialized
        initialized += 1
        arm = ("N", "A")[initialized-1]
        calls.append("initialize_" + arm)
        agent = SimpleNamespace(arm=arm, trained=False,
                                save_model=lambda path: path.write_bytes(b"checkpoint fixture"))
        identity = {"sha256": "different" if failure == "initialization" and arm == "A" else "common"}
        return agent, identity
    monkeypatch.setattr(native, "new_initialized_agent", new_agent)

    def fit(agent, config, spec, *, arm, out, summary, progress):
        calls.append("fit_" + arm)
        summary["counts"]["transitions"] = spec.transitions
        if failure == arm:
            raise RuntimeError("fixture technical failure")
        summary["status"] = "COMPLETE"
        agent.trained = True
        progress({"event": "fixture_fit_complete", "arm": arm})
    monkeypatch.setattr(training, "train_arm", fit)

    def panel(agent, config, seeds, device, *, trace_path, progress, **kwargs):
        calls.append("panel_" + trace_path.stem)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_bytes(b"trace fixture")
        worlds = []
        # N is deliberately adverse. Its score must not prevent the fixed A run.
        offset = 1.0 if not agent.trained else -10.0 if agent.arm == "N" else 2.0
        for seed in seeds:
            world = {"seed": seed, "recovery_opportunity": {},
                     **{field: offset for field in native.ENDPOINT_FIELDS}}
            progress("attempt", 1)
            progress("transition", 1)
            progress("world", world)
            worlds.append(world)
        return {"worlds": worlds, "trace_sha256": native.sha256_file(trace_path)}, {}
    monkeypatch.setattr(native, "evaluate_feedback_panel", panel)
    out = tmp_path / "batch"
    if failure:
        with pytest.raises(RuntimeError, match="fixture technical|initialization identity"):
            native.run_native(out=out, launch_sha="fixture")
    else:
        native.run_native(out=out, launch_sha="fixture")
    result = json.loads((out / "summary.json").read_text())
    assert calls[:4] == ["initialize_N", "panel_initial_development", "panel_initial_final", "fit_N"]
    if failure == "N":
        assert calls == calls[:4]
        assert result["counts"]["fits_started"] == 1
        assert result["counts"]["fits_completed"] == 0
    elif failure == "initialization":
        assert calls[-1] == "initialize_A" and "fit_A" not in calls
        assert result["counts"]["fits_completed"] == 1
    else:
        assert calls == ["initialize_N", "panel_initial_development", "panel_initial_final", "fit_N",
                         "panel_N_development", "panel_N_final", "initialize_A", "fit_A",
                         "panel_A_development", "panel_A_final"]
        assert result["status"] == "COMPLETE"
        assert result["counts"]["fits_started"] == result["counts"]["fits_completed"] == 2
        assert result["counts"]["training_transitions"] == 360000
        assert result["counts"]["evaluation_episodes_completed"] == 120
        assert result["comparisons"]["final"]["aggregate"]["effects_N_minus_initial"]["raw_native_J"]["mean"] < 0
    with pytest.raises(FileExistsError):
        native.run_native(out=out, launch_sha="fixture")
