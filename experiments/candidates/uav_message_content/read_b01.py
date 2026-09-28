"""Read-only reconstruction of the fixed B01 outputs; no policy or environment calls."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(actual, expected, atol=1e-10):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def expected_hand_packet(arm, observations, t, sender):
    raw = observations[t, :, :104]
    window = observations[max(0, t - 4):t + 1, sender, :104]
    if arm == "C":
        window = raw[sender:sender + 1]
    points = []
    for frame in window:
        users = frame[3:63].reshape(20, 3)
        points.extend(users[users[:, 2] > 0, :2] + frame[:2])
    count = len(points)
    xy = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    center = xy.mean(0) if count else np.zeros(2)
    spread = np.sqrt(np.square(xy - center).sum(1).mean() / 2) if count else 0
    return np.r_[raw[sender, :3], center, 0 if arm == "C" else spread,
                 count / (20 * len(window))]


def read_trace(row, arm):
    path = Path(row["raw"])
    assert digest(path) == row["raw_sha256"]
    with np.load(path, allow_pickle=False) as data:
        obs = data["actor_input"]
        assert obs.shape == (256, 5, 171)
        assert data["critic_input"].shape == (256, 451)
        assert data["packet"].shape == (256, 7)
        assert all(np.isfinite(data[key]).all() for key in data.files)
        pending = np.zeros(5, dtype=bool)
        records = np.zeros((5, 5, 10), dtype=np.float32)
        delivered = active = 0
        for t in range(256):
            arrived = np.flatnonzero(data["due"][:t] == t)
            for sent in arrived:
                sender = int(data["sender"][sent])
                peers = np.arange(5) != sender
                records[peers, sender, :7] = data["packet"][sent]
                records[peers, sender, 7] = 1
                records[peers, sender, 8] = sent / 256
                pending[sender] = False
            valid = records[..., 7] > 0
            records[..., 9] = np.where(valid, t / 256 - records[..., 8], 0)
            close(obs[t, :, 121:].reshape(5, 5, 10), records, 0)
            close(data["records"][t], records, 0)
            close(obs[t, :, 120], pending, 0)
            assert int(data["deliveries"][t]) == len(arrived)
            sender = t % 5
            assert int(data["sender"][t]) == sender and not pending[sender]
            due = t + (1 if data["good"][t] else 5)
            assert data["due"][t] == due
            expected_mask = arm == "L" and due < 256
            assert bool(data["content_credit_mask"][t]) == expected_mask
            active += expected_mask
            if arm == "L":
                close(data["packet"][t], np.tanh(data["pre_tanh_content"][t]), 1e-6)
            else:
                close(data["packet"][t], expected_hand_packet(arm, obs, t, sender), 2e-7)
            pending[sender] = True
            close(data["pending_after_send"][t], pending, 0)
            delivered += len(arrived)
        close(data["action"], np.tanh(data["pre_tanh_motion"]), 1e-6)
        close(data["reward_physical"], .7 * data["served_users"] / 50 + .3 * data["Q"])
        close(data["reward_net"], data["reward_physical"] - .001)
        for field, key in (("J_net", "reward_net"), ("J_physical", "reward_physical"),
                           ("served_users_per_tick", "served_users"), ("Q", "Q")):
            close(row[field], data[key].mean())
        assert delivered == row["delivered_packets"]
        assert int(pending.sum()) == row["pending_at_end"] == int((data["due"] >= 256).sum())
        assert hashlib.sha256(bytes(data["good"].tolist())).hexdigest() == row["channel_sequence_sha256"]
        return dict(delivered=delivered, censored=int(pending.sum()), content_credit_rows=active,
                    packet_coordinate_mean=data["packet"].mean(0).tolist(),
                    packet_coordinate_std=data["packet"].std(0).tolist())


def panel(arm, phase):
    return [row for row in arm["rows"] if row["phase"] == phase]


def difference(first, second, metric):
    values = [a[metric] - b[metric] for a, b in zip(first, second)]
    return dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values),
                positive_worlds=[i for i, value in enumerate(values) if value > 0],
                adverse_worlds=[i for i, value in enumerate(values) if value < 0],
                differences=values)


def read_run(root):
    summary = json.loads((root / "summary.json").read_text())
    assert summary["status"] == "COMPLETE" and summary["reduction"]["complete"]
    assert summary["actual"]["fit_started"] == 3
    assert summary["actual"]["team_steps"] == summary["actual"]["native_step_calls"] == 442368
    assert summary["actual"]["optimizer_steps"] == 3072
    assert summary["actual"]["evaluation_optimizer_steps"] == 0
    indexed = {arm["arm"]: arm for arm in summary["arms"]}
    assert set(indexed) == {"C", "H", "L"}
    metrics = ("J_net", "J_physical", "served_users_per_tick", "Q", "charge_per_tick")
    reading = dict(source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"),
                   all_checks_passed=False, native_steps_added=0, optimizer_calls_added=0,
                   model_or_policy_calls_added=0, levels={}, contrasts={}, own_learning={},
                   raw_checks={}, update_checks={}, actual=summary["actual"],
                   resources=summary["resources"],
                   batch_wall_seconds=summary["finished_wall"] - summary["started_wall"],
                   limitations=["One training instance per arm; 32 paired worlds are not training replicates.",
                                "Scene hashes certify float32 reset projections, not float64 native byte identity.",
                                "Gradient norms, parameter movement and variable packets are not semantic or causal message-use evidence."])
    for name, arm in indexed.items():
        assert len(arm["rows"]) == 576
        assert arm["counts"]["optimizer_steps"] == 1024
        reading["levels"][name] = {}
        reading["raw_checks"][name] = {}
        for phase in ("initial_eval", "final_eval"):
            rows = panel(arm, phase)
            assert [row["episode"] for row in rows] == list(range(32))
            reading["levels"][name][phase] = {key: statistics.mean(row[key] for row in rows) for key in metrics}
            reading["raw_checks"][name][phase] = [read_trace(row, name) for row in rows]
        updates = [json.loads(line) for line in (root / name / "updates.jsonl").read_text().splitlines()]
        assert [item["rollout"] for item in updates] == list(range(256))
        epochs = [epoch for item in updates for epoch in item["epochs"]]
        assert len(epochs) == 1024
        reading["update_checks"][name] = dict(
            epochs=len(epochs), gaussian_entropy_first=epochs[0]["gaussian_entropy"],
            gaussian_entropy_last=epochs[-1]["gaussian_entropy"],
            groups={group: dict(nonzero_updates=sum(row["grad_groups"][group] > 0 for row in epochs),
                                minimum=min(row["grad_groups"][group] for row in epochs),
                                maximum=max(row["grad_groups"][group] for row in epochs))
                    for group in epochs[0]["grad_groups"]})
        for key in ("initial_checkpoint", "final_checkpoint"):
            assert digest(Path(arm[key]["path"])) == arm[key]["sha256"]
        reading["own_learning"][name] = {
            key: difference(panel(arm, "final_eval"), panel(arm, "initial_eval"), key) for key in metrics}
    for first, second in (("L", "H"), ("L", "C"), ("H", "C")):
        label = f"{first}-{second}"
        reading["contrasts"][label] = {}
        for phase in ("train", "initial_eval", "final_eval"):
            a, b = panel(indexed[first], phase), panel(indexed[second], phase)
            assert len(a) == len(b)
            for x, y in zip(a, b):
                for key in ("reset_seed", "channel_seed", "initial_scene_sha256", "channel_sequence_sha256"):
                    assert x[key] == y[key]
            if phase != "train":
                reading["contrasts"][label][phase] = {key: difference(a, b, key) for key in metrics}
                for key in metrics:
                    close(reading["contrasts"][label][phase][key]["differences"],
                          summary["reduction"]["comparisons"][label][phase][key]["differences"], 0)
    reading["mutable_status_excluded"] = "launch-status.json is refreshed by native status observations."
    reading["files"] = [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                         "sha256": digest(path)} for path in sorted(root.rglob("*"))
                        if path.is_file() and path.name not in ("reading.json", "launch-status.json")]
    reading["durable_root"] = str(root)
    reading["durable_bytes"] = sum(item["bytes"] for item in reading["files"])
    reading["all_checks_passed"] = True
    return reading


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = read_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"all_checks_passed": result["all_checks_passed"],
                      "files": len(result["files"]), "durable_bytes": result["durable_bytes"]}))
