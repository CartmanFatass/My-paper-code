import json
import time

import torch

from experiments.candidates.acvc.cluster_paired_exposure_b01 import protocol as p
from scripts import run_acvc_cluster_paired_exposure_b01 as runner


class Model:
    def __init__(self, value=0):
        self.value = value

    def state_dict(self):
        return {"value": torch.tensor(self.value)}


def test_expired_invocation_publishes_incomplete_and_nonzero_exit(tmp_path):
    output = tmp_path / "expired"
    assert runner.run(output, "f" * 40, time.monotonic() - 2, 1) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert "TimeoutError" in summary["error"]
    assert summary["training_rows"] == 0 and summary["evaluation_rows"] == 0
    assert summary["counts"]["fixed_snapshots"] == 0
    assert summary["primary"]["changes"]["G_dwell"]["reading"] == "INCOMPLETE"
    assert "262144 training team steps" in summary["cost_law"]


def test_fixed_training_checkpoint_and_private_evaluation_order(tmp_path, monkeypatch):
    events = []
    envs = []
    bases = []

    monkeypatch.setattr(runner.shared, "templates", lambda _seed: (Model(), Model()))
    monkeypatch.setattr(runner.shared, "NativeGeometryActor", lambda actor, *_args: actor)
    monkeypatch.setattr(runner.shared, "geometry_snapshot", lambda actor, critic: (actor.value, critic.value))
    monkeypatch.setattr(runner.shared, "geometry_exposure",
                        lambda initial, actor, critic: {"actor_displacement": actor.value - initial[0],
                                                        "critic_displacement": critic.value - initial[1]})
    monkeypatch.setattr(runner.shared, "optimizer_for", lambda *_args: object())
    monkeypatch.setattr(runner.shared, "generator", lambda seed: ("generator", seed))
    monkeypatch.setattr(runner.shared, "parameter_count", lambda *_args: 1)
    monkeypatch.setattr(runner.shared, "clean_json", lambda value, _limits: value)
    monkeypatch.setattr(runner.shared, "write_json",
                        lambda path, value: path.write_text(json.dumps(value), encoding="utf-8"))

    def make_env(seed):
        env = object()
        envs.append((seed, env))
        return env

    monkeypatch.setattr(runner, "make_cluster", make_env)

    def collect_episode(env, actor, critic, horizon, reset_seed, velocity, duration, identity,
                        check, counts, emit, *_args, **_kwargs):
        assert env is envs[0][1]
        counts["train_episodes"] += 1
        counts["team_steps"] += horizon
        counts["train_team_steps"] += horizon
        counts["completed_episode_steps"] += horizon
        counts["step_calls"] += horizon
        counts["explicit_resets"] += 1
        emit(dict(identity, reset_seed=reset_seed, steps=horizon, reward_sum=1.0, J=1.0 / horizon))
        events.append(("train", identity["episode"], actor.value))
        return object()

    monkeypatch.setattr(runner.shared, "collect_episode", collect_episode)

    def update(actor, critic, optimizer, episodes, chunk, check, counts, **_kwargs):
        actor.value += 1
        critic.value += 1
        counts["optimizer_steps"] += 4
        return [{"epoch": epoch} for epoch in range(4)]

    monkeypatch.setattr(runner.shared, "update", update)
    original_save = runner._save_checkpoint

    def save(path, actor, critic, checkpoint_episode):
        events.append(("save", checkpoint_episode, actor.value))
        original_save(path, actor, critic, checkpoint_episode)

    monkeypatch.setattr(runner, "_save_checkpoint", save)

    def load(path, namespace):
        payload = torch.load(path, weights_only=True)
        base = object()
        bases.append((path.name, namespace, base, int(payload["actor"]["value"])))
        events.append(("load", payload["checkpoint_episode"], path.name))
        return base

    monkeypatch.setattr(runner.shared, "load_base", load)

    def collect(env, base, _a, _b, namespace, arm, phase, episode, horizon, check, counts, emit):
        assert phase == "eval"
        counts["eval_episodes"] += 1
        counts["team_steps"] += horizon
        counts["step_calls"] += horizon
        counts["explicit_resets"] += 1
        value = {"C": .10, "F": .13, "dwell": .11}[arm]
        emit({"phase": phase, "arm": arm, "episode": episode,
              "reset_seed": 100000 * namespace + 2000 + episode,
              "steps": horizon, "J": value, "S": value * horizon})
        events.append(("eval", namespace, arm, episode, env, base))

    monkeypatch.setattr(runner.shared, "collect", collect)

    output = tmp_path / "run"
    assert runner.run(output, "f" * 40, runner.time.monotonic(), 60) == 0
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "complete"
    assert summary["training_rows"] == 1024 and summary["evaluation_rows"] == 384
    assert summary["counts"]["rollouts"] == 512
    assert summary["counts"]["optimizer_steps"] == 2048
    assert summary["counts"]["update_records"] == 2048
    assert summary["counts"]["fixed_snapshots"] == 2
    assert summary["counts"]["post_fit_loads"] == 6
    assert summary["counts"]["environment_constructors"] == 7
    assert summary["counts"]["team_steps"] == 360448
    assert summary["checkpoints"] == [
        {"checkpoint_episode": 512, "completed_rollout_index": 255,
         "optimizer_steps": 1024, "update_records": 1024, "path": "DENSE_episode_512.pt"},
        {"checkpoint_episode": 1024, "completed_rollout_index": 511,
         "optimizer_steps": 2048, "update_records": 2048, "path": "DENSE_episode_1024.pt"},
    ]
    assert events[511] == ("train", 511, 255)
    assert ("save", 512, 256) in events and ("save", 1024, 512) in events
    assert max(i for i, event in enumerate(events) if event[0] == "train") \
        < min(i for i, event in enumerate(events) if event[0] == "load")
    assert int(torch.load(output / "DENSE_episode_512.pt", weights_only=True)["actor"]["value"]) == 256
    assert int(torch.load(output / "DENSE_episode_1024.pt", weights_only=True)["actor"]["value"]) == 512
    updates = [json.loads(line) for line in (output / "updates.jsonl").read_text().splitlines()]
    assert [(row["rollout"], row["epoch"], row["episodes"]) for row in updates] == [
        (index // 4, index % 4, [2 * (index // 4), 2 * (index // 4) + 1])
        for index in range(2048)
    ]
    assert [(name, namespace, value) for name, namespace, _base, value in bases] == [
        (f"DENSE_episode_{checkpoint}.pt", p.EVALUATION_NAMESPACE, checkpoint // 2)
        for checkpoint, _arm in p.EVALUATION_ORDER
    ]
    assert len({id(base) for _name, _namespace, base, _value in bases}) == 6
    assert len({id(env) for _seed, env in envs[1:]}) == 6
    assert [seed for seed, _env in envs[1:]] == [
        100000 * p.EVALUATION_NAMESPACE + 60 + {"C": 2, "F": 3, "dwell": 4}[arm]
        for _checkpoint, arm in p.EVALUATION_ORDER
    ]
    eval_rows = [json.loads(line) for line in (output / "episodes.jsonl").read_text().splitlines()
                 if json.loads(line).get("phase") == "eval"]
    assert [(row["checkpoint_episode"], row["arm"]) for row in eval_rows[::64]] == list(p.EVALUATION_ORDER)
    for checkpoint in p.CHECKPOINTS:
        selected = [row for row in eval_rows if row["checkpoint_episode"] == checkpoint]
        assert {row["reset_seed"] for row in selected} == {
            100000 * p.EVALUATION_NAMESPACE + 2000 + episode for episode in range(64)
        }
    assert "2 fixed snapshot serializations + 6 checkpoint loads" in summary["cost_law"]
