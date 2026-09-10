import importlib.util
import json
from pathlib import Path
import time

import pytest
import torch


class FakeModule:
    def __init__(self, value):
        self.value = value

    def state_dict(self):
        return {"weight": torch.tensor([self.value], dtype=torch.float32)}


def test_fresh_dense_orchestration_counts_and_publication(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_fresh_dense_reuse_b01.py"
    spec = importlib.util.spec_from_file_location("fresh_dense_b01_runner", script)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _threads: None)
    spec.loader.exec_module(module)

    alarm = {"armed": False, "events": [], "handlers": []}

    def fake_signal(_number, handler):
        alarm["handlers"].append(handler)
        return "outer-handler"

    def fake_setitimer(_timer, seconds):
        alarm["armed"] = seconds > 0
        alarm["events"].append(seconds)

    monkeypatch.setattr(module.signal, "SIGALRM", 1001, raising=False)
    monkeypatch.setattr(module.signal, "ITIMER_REAL", 1002, raising=False)
    monkeypatch.setattr(module.signal, "signal", fake_signal)
    monkeypatch.setattr(module.signal, "setitimer", fake_setitimer, raising=False)
    source_final_panel = module.final_panel
    finalization_alarm_states = []

    def observed_final_panel(rows, expected):
        finalization_alarm_states.append(alarm["armed"])
        return source_final_panel(rows, expected)

    monkeypatch.setattr(module, "final_panel", observed_final_panel)

    calls = {"templates": [], "dense": [], "generators": [], "envs": [],
             "training": [], "updates": [], "loads": [], "evaluation": []}

    def fake_templates(seed):
        calls["templates"].append(seed)
        return FakeModule(1), FakeModule(2)

    def fake_dense(common, kind, seed):
        calls["dense"].append((common, kind, seed))
        return FakeModule(3)

    def fake_generator(seed):
        stream = {"seed": seed}
        calls["generators"].append(stream)
        return stream

    def fake_collect_episode(env, actor, critic, horizon, reset_seed, velocity_rng,
                             duration_rng, metadata, check, counts, emit_episode,
                             emit_diagnostic, limits, **options):
        check()
        calls["training"].append({
            "env": env, "reset_seed": reset_seed, "velocity_rng": velocity_rng,
            "duration_rng": duration_rng, "metadata": metadata, "options": options,
        })
        counts["explicit_resets"] += 1
        counts["step_calls"] += horizon
        counts["team_steps"] += horizon
        counts["train_team_steps"] += horizon
        counts["completed_episode_steps"] += horizon
        counts["train_episodes"] += 1
        counts["recurrent_observations"] += 5 * horizon
        counts["velocity_decisions"] += 5 * horizon
        counts["scientific_uav_calls"] += horizon
        emit_episode(dict(metadata, reset_seed=reset_seed, steps=horizon,
                          reward_sum=float(metadata["episode"]),
                          J=float(metadata["episode"]) / horizon))
        return {"episode": metadata["episode"]}

    def fake_update(actor, critic, optimizer, episodes, chunk, check, counts, **options):
        check()
        calls["updates"].append({
            "episodes": episodes, "chunk": chunk, "options": options,
        })
        counts["optimizer_steps"] += 4
        return [{"epoch": epoch, "loss": float(epoch)} for epoch in range(4)]

    def fake_load(path, seed):
        calls["loads"].append((Path(path), seed))
        return FakeModule(4)

    arm_scores = {"C": 0.0, "F": 0.02, "dwell": 0.005}

    def fake_collect(env, base, gate, critic, seed, arm, phase, episode,
                     horizon, check, counts, emit):
        check()
        calls["evaluation"].append((env, seed, arm, phase, episode, horizon))
        counts["explicit_resets"] += 1
        counts["step_calls"] += horizon
        counts["team_steps"] += horizon
        counts["eval_episodes"] += 1
        counts["base_agent_forwards"] += 5 * horizon
        value = arm_scores[arm] + episode * 0.001
        emit({
            "arm": arm, "phase": phase, "episode": episode,
            "reset_seed": seed * 100000 + 2000 + episode,
            "steps": horizon, "S": value * horizon, "J": value,
            "opportunities": episode + 1 if arm != "C" else 0,
            "retrace": episode + 1 if arm == "F" else 0,
            "dwell": episode + 1 if arm == "dwell" else 0,
            "apply": horizon, "distinguishable": episode if arm != "C" else 0,
        })

    def fake_env(seed):
        value = {"constructor_seed": seed}
        calls["envs"].append(value)
        return value

    monkeypatch.setattr(module, "templates", fake_templates)
    monkeypatch.setattr(module, "NativeGeometryActor", fake_dense)
    monkeypatch.setattr(module, "generator", fake_generator)
    monkeypatch.setattr(module, "collect_episode", fake_collect_episode)
    monkeypatch.setattr(module, "optimizer_for", lambda actor, critic: object())
    monkeypatch.setattr(module, "update", fake_update)
    monkeypatch.setattr(module, "load_base", fake_load)
    monkeypatch.setattr(module, "collect", fake_collect)
    monkeypatch.setattr(module, "geometry_snapshot",
                        lambda actor, critic: {"total": torch.tensor([0.0])})
    monkeypatch.setattr(module, "geometry_exposure", lambda initial, actor, critic: {
        "total": {"parameters": 2, "initial_norm": 0.0, "final_norm": 1.0,
                  "displacement": 1.0, "relative_displacement": None}
    })
    monkeypatch.setattr(module, "parameter_count",
                        lambda actor, critic=None: 69079 if critic is not None else
                        34177 if actor.value == 2 else 34902)

    output = tmp_path / "complete"
    code = module.run(output, "synthetic", time.monotonic(), 20.0,
                      make_env=fake_env, train_episodes=4, horizon=8, eval_episodes=3)
    assert code == 0
    assert calls["templates"] == [8921]
    assert calls["dense"][0][1:] == (module.DENSE, 892100012)
    assert [item["constructor_seed"] for item in calls["envs"]] == [
        892101000, 892200062, 892200063, 892200064,
    ]
    assert [item[1] for item in calls["loads"]] == [8922, 8922, 8922]
    assert [item[2] for item in calls["evaluation"]] == [
        arm for arm in ("C", "F", "dwell") for _episode in range(3)
    ]
    assert [item["reset_seed"] for item in calls["training"]] == [
        892101000, 892101001, 892101002, 892101003,
    ]
    assert len({id(item["velocity_rng"]) for item in calls["training"]}) == 1
    assert [item["duration_rng"]["seed"] for item in calls["training"]] == [
        892104000, 892104001, 892104002, 892104003,
    ]
    assert all(item["options"] == {
        "real": True, "diagnostics": False,
        "ratio_grouping": "agent_compound", "value_moments": None,
        "renewal": False, "duration_support": (1, 4),
        "velocity_mode": "sampled",
    } for item in calls["training"])
    assert len(calls["updates"]) == 2
    assert all(item["chunk"] == 32 and item["options"] == {
        "ratio_grouping": "agent_compound", "entropy_coef": 0.01,
        "value_moments": None,
    } for item in calls["updates"])

    saved = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert saved["status"] == "complete"
    assert saved["fit_complete"] and saved["checkpoint_complete"]
    assert saved["training_rows"] == 4 and saved["evaluation_rows"] == 9
    assert saved["counts"]["team_steps"] == 104
    assert saved["counts"]["train_team_steps"] == 32
    assert saved["counts"]["eval_team_steps"] == 72
    assert saved["counts"]["optimizer_steps"] == 8
    assert saved["counts"]["backward_calls"] == 8
    assert saved["counts"]["backward_calls_lower_bound"] == 8
    assert saved["counts"]["update_records"] == 8
    assert saved["counts"]["replayed_actor_agent_steps"] == 640
    assert saved["counts"]["replayed_actor_agent_steps_lower_bound"] == 640
    assert saved["counts"]["critic_update_rows"] == 128
    assert saved["counts"]["critic_update_rows_lower_bound"] == 128
    assert saved["counts"]["fresh_dense_initializations"] == 1
    assert saved["counts"]["post_fit_loads"] == 3
    assert saved["parameters"] == {"actor": 34902, "critic": 34177, "total": 69079}
    assert saved["primary"]["primaries"] == ["F-C", "F-dwell"]
    assert saved["primary"]["contrasts"]["F-C"]["mean_J"] == pytest.approx(0.02)
    assert saved["primary"]["contrasts"]["F-dwell"]["mean_J"] == pytest.approx(0.015)
    assert saved["primary"]["contrasts"]["F-C"]["conditional_SE_J"] == pytest.approx(0.0)
    assert len((output / "episodes.jsonl").read_text(encoding="utf-8").splitlines()) == 13
    assert len((output / "updates.jsonl").read_text(encoding="utf-8").splitlines()) == 8
    assert (output / "final_DENSE.pt").exists()
    assert finalization_alarm_states == [False]
    assert alarm["events"][-1] == 0
    assert alarm["handlers"][-1] == "outer-handler"

    complete_collect = module.collect
    evaluation_calls = 0

    def fail_after_one(*args, **kwargs):
        nonlocal evaluation_calls
        if evaluation_calls == 1:
            raise RuntimeError("synthetic panel failure")
        evaluation_calls += 1
        return complete_collect(*args, **kwargs)

    monkeypatch.setattr(module, "collect", fail_after_one)
    partial = tmp_path / "partial"
    assert module.run(partial, "synthetic", time.monotonic(), 20.0,
                      make_env=fake_env, train_episodes=4, horizon=8,
                      eval_episodes=3) == 1
    failed = json.loads((partial / "summary.json").read_text(encoding="utf-8"))
    assert failed["status"] == "incomplete"
    assert failed["fit_complete"] and failed["checkpoint_complete"]
    assert failed["evaluation_rows"] == 1
    assert failed["error"] == "RuntimeError: synthetic panel failure"
    assert len((partial / "episodes.jsonl").read_text(encoding="utf-8").splitlines()) == 5

    monkeypatch.setattr(module, "collect", complete_collect)

    def interrupted_update(actor, critic, optimizer, episodes, chunk, check,
                           counts, **options):
        counts["optimizer_steps"] += 2
        raise RuntimeError("synthetic interrupted update")

    monkeypatch.setattr(module, "update", interrupted_update)
    interrupted = tmp_path / "interrupted-update"
    assert module.run(interrupted, "synthetic", time.monotonic(), 20.0,
                      make_env=fake_env, train_episodes=4, horizon=8,
                      eval_episodes=3) == 1
    stopped = json.loads((interrupted / "summary.json").read_text(encoding="utf-8"))
    assert stopped["status"] == "incomplete"
    assert stopped["counts"]["optimizer_steps"] == 2
    assert stopped["counts"]["update_records"] == 0
    assert stopped["counts"]["backward_calls"] is None
    assert stopped["counts"]["replayed_actor_agent_steps"] is None
    assert stopped["counts"]["critic_update_rows"] is None
    assert stopped["counts"]["backward_calls_lower_bound"] == 2
    assert stopped["counts"]["replayed_actor_agent_steps_lower_bound"] == 160
    assert stopped["counts"]["critic_update_rows_lower_bound"] == 32
    assert stopped["interrupted_update"] == {
        "rollout": 0,
        "completed_adam_steps": 2,
        "completed_adam_epoch_records_missing": 2,
        "record_limit": (
            "The protected four-epoch update helper returned no partial epoch list; "
            "no values are claimed for the missing records."
        ),
    }
    assert stopped["unavailable_measurements"] == [
        "exact backward calls across the interrupted update",
        "exact replayed actor-agent steps across the interrupted update",
        "exact critic update rows across the interrupted update",
    ]
    assert stopped["training_rows"] == 2 and stopped["evaluation_rows"] == 0
    assert not stopped["fit_complete"] and not stopped["checkpoint_complete"]
    assert not (interrupted / "final_DENSE.pt").exists()
    assert (interrupted / "updates.jsonl").read_text(encoding="utf-8") == ""
    assert finalization_alarm_states == [False, False, False]
