"""Fixed B09 protocol, outcome blindness, partial failure and no output reuse."""

import json
import gzip
from types import SimpleNamespace

import pytest

from experiments.candidates.uav_service_auxiliary.b09 import native, training


@pytest.mark.parametrize("failure", (None, "N", "initialization"))
def test_fixed_batch_uses_one_primary_panel_and_never_retries(tmp_path, monkeypatch, failure):
    calls = []
    initialized = 0
    monkeypatch.setattr(native.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(native.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(native, "make_b09_config", lambda spec: SimpleNamespace())
    monkeypatch.setattr(native, "fixed_config_record", lambda spec, config: {"fixture": True})

    def new_agent(*args, **kwargs):
        nonlocal initialized
        initialized += 1
        arm = ("N", "A")[initialized - 1]
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
        progress({"event": "training_exit", "arm": arm})
    monkeypatch.setattr(training, "train_arm", fit)

    def panel(agent, config, seeds, device, *, trace_path, progress, **kwargs):
        calls.append("panel_" + trace_path.stem)
        assert tuple(seeds) == native.PRIMARY_SEEDS
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_bytes(b"trace fixture")
        worlds = []
        offset = 1.0 if not agent.trained else -10.0 if agent.arm == "N" else 2.0
        for seed in seeds:
            world = {"seed": seed, "recovery_opportunity": {
                         "intervals": [{"member": 0, "start_step": 0}],
                         "first_qualifying_exit_anchor": None,
                         "denominators": {"feedback_activation_intervals": 1}},
                     "service_free_intervals": [{"start_step": 2, "actual_steps": 3}],
                     "service_free_interval_count": 1,
                     "mode_durations_by_uav": [[2], [], [], [], [], [], [], []],
                     "descriptive_250_step_bins": [{"actual_steps": 250, "qos_sum": 4.0}],
                     "first_half": {"actual_steps": 1500, "qos_sum": 8.0},
                     "second_half": {"actual_steps": 1500, "qos_sum": 9.0},
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
    assert calls[:3] == ["initialize_N", "panel_initial_primary", "fit_N"]
    assert result["counts"]["evaluation_episodes_completed"] == (32 if failure == "N" else
                                                              64 if failure == "initialization" else 96)
    if failure == "N":
        assert calls == calls[:3]
        assert result["counts"]["fits_started"] == 1
        assert result["counts"]["fits_completed"] == 0
    elif failure == "initialization":
        assert calls[-1] == "initialize_A" and "fit_A" not in calls
        assert result["counts"]["fits_completed"] == 1
    else:
        assert calls == ["initialize_N", "panel_initial_primary", "fit_N", "panel_N_primary",
                         "initialize_A", "fit_A", "panel_A_primary"]
        assert result["status"] == "COMPLETE"
        assert result["counts"]["fits_started"] == result["counts"]["fits_completed"] == 2
        assert result["counts"]["training_transitions"] == 360000
        assert result["comparisons"]["primary"]["aggregate"]["effects_N_minus_initial"]["raw_native_J"]["mean"] < 0
    assert len(result["evaluations"]) == (1 if failure == "N" else 2 if failure else 3)
    assert "intervals" not in result["evaluations"]["initial_primary"]["worlds"][0]["recovery_opportunity"]
    with gzip.open(out / "raw" / "evaluation_initial_primary.json.gz", "rt") as handle:
        raw = json.load(handle)
    assert raw["worlds"][0]["recovery_opportunity"]["intervals"][0]["member"] == 0
    compact_world = result["evaluations"]["initial_primary"]["worlds"][0]
    raw_world = raw["worlds"][0]
    for field in ("service_free_intervals", "mode_durations_by_uav",
                  "descriptive_250_step_bins"):
        assert field not in compact_world
        assert field in raw_world and raw_world[field]
    assert compact_world["service_free_interval_count"] == 1
    assert compact_world["first_half"] == raw_world["first_half"]
    assert compact_world["second_half"] == raw_world["second_half"]
    assert "raw/evaluation_initial_primary.json.gz" in result["artifacts"]
    with pytest.raises(FileExistsError):
        native.run_native(out=out, launch_sha="fixture")
