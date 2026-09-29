"""Reconstruct B02 from retained arrays and streams without policy or environment calls."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np


MASTERS = (19451, 19452, 19453)
ARMS = ("B", "O", "L")
METRICS = ("J_net", "J_physical", "served_users_per_tick", "Q", "charge_per_tick")
CHECKPOINT_SHA = "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(actual, expected, atol=1e-10):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def packet_from_observations(observations, t, sender, arm):
    raw = observations[t, sender, :104]
    users = raw[3:63].reshape(20, 3)
    valid = users[:, 2] > 0
    count = int(valid.sum())
    centroid = (users[valid, :2].mean(0) + raw[:2]) if count else np.zeros(2)
    packet = np.r_[raw[:3], centroid, 0., count / 20]
    if arm == "O":
        points = []
        for frame in observations[max(0, t - 4):t + 1, sender, :104]:
            rows = frame[3:63].reshape(20, 3)
            points.extend(rows[rows[:, 2] > 0, :2] + frame[:2])
        if points:
            xy = np.asarray(points, dtype=np.float64)
            # Independent centered calculation, rather than the runner's moments.
            variance = np.square(xy - xy.mean(0)).sum(1).mean()
            packet[5] = np.clip(np.sqrt(2 * variance), 0, 1)
    return packet


def read_trace(row, arm):
    path = Path(row["raw"])
    assert digest(path) == row["raw_sha256"]
    with np.load(path, allow_pickle=False) as data:
        obs = data["actor_input"]
        assert obs.shape == (256, 5, 171)
        assert data["critic_input"].shape == (256, 451)
        assert data["packet"].shape == (256, 7)
        assert data["pre_tanh_content"].shape == (256, 1)
        assert all(np.isfinite(data[key]).all() for key in data.files)
        close(data["critic_input"][:, 136:].reshape(256, 5, 63), obs[:, :, 108:], 0)
        close(obs[:, :, 107], 0, 0)
        close(obs[0, :, 104:107], 0, 0)
        close(obs[1:, :, 104:107], data["action"][:-1], 0)
        close(obs[:, :, 110:115], np.broadcast_to(np.eye(5), (256, 5, 5)), 0)
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
            records[..., 9] = np.where(records[..., 7] > 0, t / 256 - records[..., 8], 0)
            close(obs[t, :, 121:].reshape(5, 5, 10), records, 0)
            close(data["records"][t], records, 0)
            close(obs[t, :, 120], pending, 0)
            assert int(data["deliveries"][t]) == len(arrived)
            sender = t % 5
            assert int(data["sender"][t]) == sender and not pending[sender]
            close(obs[t, :, 108:110], np.tile(np.eye(2)[int(data["good"][t])], (5, 1)), 0)
            close(obs[t, :, 115:120], np.tile(np.eye(5)[sender], (5, 1)), 0)
            due = t + (1 if data["good"][t] else 5)
            assert int(data["due"][t]) == due
            mask = arm == "L" and due < 256
            assert bool(data["content_credit_mask"][t]) == mask
            active += mask
            expected = packet_from_observations(obs, t, sender, arm)
            if arm == "L":
                expected[5] = (1 + np.tanh(data["pre_tanh_content"][t, 0])) / 2
            close(data["packet"][t], expected, 3e-7)
            assert 0 <= float(data["packet"][t, 5]) <= 1
            pending[sender] = True
            close(data["pending_after_send"][t], pending, 0)
            delivered += len(arrived)
        close(data["action"], np.tanh(data["pre_tanh_motion"]), 1e-6)
        assert hashlib.sha256(data["action"].tobytes()).hexdigest() == row["action_sequence_sha256"]
        close(data["reward_physical"], .7 * data["served_users"] / 50 + .3 * data["Q"])
        close(data["reward_net"], data["reward_physical"] - .001)
        for field, key in (("J_net", "reward_net"), ("J_physical", "reward_physical"),
                           ("served_users_per_tick", "served_users"), ("Q", "Q")):
            close(row[field], data[key].mean())
        close(row["charge_per_tick"], .001)
        assert delivered == row["delivered_packets"]
        assert int(pending.sum()) == row["pending_at_end"] == int((data["due"] >= 256).sum())
        assert hashlib.sha256(bytes(data["good"].tolist())).hexdigest() == row["channel_sequence_sha256"]
        response_rms = np.asarray(data["scalar_response_rms"], dtype=np.float64)
        response_max = np.asarray(data["scalar_response_max"], dtype=np.float64)
        assert response_rms.shape == response_max.shape == (256,)
        assert np.all(response_rms >= 0) and np.all(response_max >= response_rms - 1e-7)
        close(row["scalar_response_rms"], np.sqrt(np.square(response_rms).mean()), 1e-7)
        close(row["scalar_response_max"], response_max.max(), 1e-7)
        if arm == "B" or row["phase"] == "initial_eval":
            close(response_rms, 0, 0)
            close(response_max, 0, 0)
        xyz = obs[:, :, :3]
        behavior = {
            "boundary_fraction": np.any((xyz[:, :, :2] <= 1e-7) |
                                         (xyz[:, :, :2] >= 1 - 1e-7), axis=-1).mean(),
            "height_floor_fraction": (xyz[:, :, 2] <= 1e-7).mean(),
            "height_ceiling_fraction": (xyz[:, :, 2] >= 1 - 1e-7).mean(),
            "mean_height_m": (50 + 100 * xyz[:, :, 2].astype(np.float64)).mean(),
        }
        for key, value in behavior.items():
            close(row[key], value, 2e-5 if key == "mean_height_m" else 1e-7)
        return dict(delivered=delivered, censored=int(pending.sum()), content_credit_rows=active,
                    scalar_mean=float(data["packet"][:, 5].mean()),
                    scalar_std=float(data["packet"][:, 5].std()),
                    scalar_response_rms=float(row["scalar_response_rms"]),
                    scalar_response_max=float(row["scalar_response_max"]),
                    action_sha256=hashlib.sha256(data["action"].tobytes()).hexdigest(),
                    reward_sha256=hashlib.sha256(data["reward_net"].tobytes()).hexdigest(),
                    **{key: float(value) for key, value in behavior.items()})


def panel(rows, phase):
    return [row for row in rows if row["phase"] == phase]


def differences(first, second, metric):
    assert len(first) == len(second) == 32
    values = [a[metric] - b[metric] for a, b in zip(first, second)]
    return dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values),
                positive_worlds=[i for i, value in enumerate(values) if value > 0],
                adverse_worlds=[i for i, value in enumerate(values) if value < 0],
                differences=values)


def seed_summary(values):
    assert len(values) == 3
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    half_width = 4.302652729911275 * sd / np.sqrt(3)
    return dict(per_continuation_seed=values, mean=mean, sample_sd=sd,
                descriptive_t95_df2=[mean - half_width, mean + half_width],
                positive=sum(value > 0 for value in values),
                adverse=sum(value < 0 for value in values))


def read_run(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    assert summary["status"] == "COMPLETE"
    assert summary["warm_start"]["sha256"] == CHECKPOINT_SHA
    assert digest(summary["warm_start"]["path"]) == CHECKPOINT_SHA
    cells = {(int(cell["master"]), cell["arm"]): cell for cell in summary["cells"]}
    assert set(cells) == {(seed, arm) for seed in MASTERS for arm in ARMS}
    actual = summary["actual"]
    for key, value in dict(fit_started=9, train_episodes=4608,
                           initial_eval_episodes=288, final_eval_episodes=288,
                           train_team_steps=1179648, team_steps=1327104,
                           native_step_calls=1327104, optimizer_steps=9216,
                           replayed_actor_rows=23592960, motion_samples=6635520,
                           diagnostic_forward_calls=147456,
                           evaluation_optimizer_steps=0).items():
        assert actual[key] == value, (key, actual[key], value)
    reading = dict(source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"),
                   all_checks_passed=False, native_steps_added=0, optimizer_calls_added=0,
                   model_or_policy_calls_added=0, levels={}, contrasts={}, own_learning={},
                   seed_contrasts={}, raw_checks={}, update_checks={}, actual=actual,
                   resources=summary["resources"],
                   batch_wall_seconds=summary["finished_wall"] - summary["started_wall"],
                   limitations=["Three independent continuations conditional on one selected C checkpoint and one fixed evaluation panel.",
                                "Initial equality is checked on all declared sampled evaluation trajectories, not a finite-training guarantee.",
                                "The df2 interval assumes independent continuation contrasts; evaluation worlds are nested, not extra training seeds.",
                                "Local scalar sensitivity and content movement do not identify semantic information or full-task causal use.",
                                "Boundary and height are pre-action behavioral readings, not energy or physical safety outcomes."])
    all_rows = {}
    initial_reference = None
    for seed in MASTERS:
        for arm in ARMS:
            cell = cells[(seed, arm)]
            label = f"{seed}/{arm}"
            folder = Path(cell["directory"])
            rows = [json.loads(line) for line in (folder / "episodes.jsonl").read_text().splitlines()]
            all_rows[(seed, arm)] = rows
            assert len(rows) == 576 and cell["status"] == "COMPLETE"
            assert len(cell["rows"]) == 64
            assert cell["counts"]["optimizer_steps"] == 1024
            assert cell["counts"]["evaluation_optimizer_steps"] == 0
            assert cell["counts"]["team_steps"] == 147456
            assert cell["counts"]["diagnostic_forward_calls"] == 16384
            assert cell["warm_start"]["sha256"] == CHECKPOINT_SHA
            for phase, count in (("train", 512), ("initial_eval", 32), ("final_eval", 32)):
                selected = panel(rows, phase)
                assert [row["episode"] for row in selected] == list(range(count))
                for e, row in enumerate(selected):
                    base = 100000 * seed if phase == "train" else 1945000000
                    assert row["reset_seed"] == base + (1000 if phase == "train" else 2000) + e
                    assert row["channel_seed"] == base + (6000 if phase == "train" else 7000) + e
                    assert row["motion_seed"] == base + (21 if phase == "train" else 3000 + e)
                    assert row["content_seed"] == base + (22 if phase == "train" else 4000 + e)
                    assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
                    assert row["collided_attempts"] == 0
                    close(row["charge_per_tick"], .001)
                assert sum(row["delivered_packets"] for row in selected) == cell["counts"][f"{phase}_delivered_packets"]
                assert sum(row["pending_at_end"] for row in selected) == cell["counts"][f"{phase}_censored_packets"]
                assert all(row["delivered_packets"] + row["pending_at_end"] == 256 for row in selected)
                assert cell["counts"][f"{phase}_content_credit_rows"] == (
                    sum(row["delivered_packets"] for row in selected) if arm == "L" else 0)
            reading["levels"][label], reading["raw_checks"][label] = {}, {}
            for phase in ("initial_eval", "final_eval"):
                selected = panel(rows, phase)
                assert selected == panel(cell["rows"], phase)
                reading["levels"][label][phase] = {key: statistics.mean(row[key] for row in selected)
                                                   for key in METRICS}
                checked = [read_trace(row, arm) for row in selected]
                reading["raw_checks"][label][phase] = checked
                if phase == "initial_eval":
                    identity = [(item["action_sha256"], item["reward_sha256"]) for item in checked]
                    if initial_reference is None:
                        initial_reference = identity
                    assert identity == initial_reference
            epochs = [json.loads(line) for line in (folder / "updates.jsonl").read_text().splitlines()]
            assert [(item["rollout"], item["epoch"]) for item in epochs] == [
                (rollout, epoch) for rollout in range(256) for epoch in range(4)]
            assert len(epochs) == 1024
            reading["update_checks"][label] = dict(
                epochs=len(epochs), gaussian_entropy_first=epochs[0]["gaussian_entropy"],
                gaussian_entropy_last=epochs[-1]["gaussian_entropy"],
                groups={group: dict(nonzero_updates=sum(row["grad_groups"][group] > 0 for row in epochs),
                                    minimum=min(row["grad_groups"][group] for row in epochs),
                                    maximum=max(row["grad_groups"][group] for row in epochs))
                        for group in epochs[0]["grad_groups"]})
            for key in ("initial_checkpoint", "final_checkpoint"):
                assert digest(cell[key]["path"]) == cell[key]["sha256"]
            reading["own_learning"][label] = {
                key: differences(panel(rows, "final_eval"), panel(rows, "initial_eval"), key)
                for key in METRICS}
    reference = cells[(MASTERS[0], "B")]["initial_tensor_sha256"]
    for cell in cells.values():
        for group in ("motion_receiver", "critic"):
            assert cell["initial_tensor_sha256"][group] == reference[group]
    for seed in MASTERS:
        for first, second in (("L", "B"), ("L", "O"), ("O", "B")):
            label = f"{seed}/{first}-{second}"
            reading["contrasts"][label] = {}
            for phase in ("train", "initial_eval", "final_eval"):
                a, b = panel(all_rows[(seed, first)], phase), panel(all_rows[(seed, second)], phase)
                for x, y in zip(a, b):
                    for key in ("reset_seed", "channel_seed", "initial_scene_sha256", "channel_sequence_sha256"):
                        assert x[key] == y[key]
                if phase != "train":
                    reading["contrasts"][label][phase] = {key: differences(a, b, key) for key in METRICS}
    for comparison in ("L-B", "L-O", "O-B"):
        reading["seed_contrasts"][comparison] = {
            key: seed_summary([reading["contrasts"][f"{seed}/{comparison}"]["final_eval"][key]["mean"]
                               for seed in MASTERS]) for key in METRICS}
    reading["files"] = [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                         "sha256": digest(path)} for path in sorted(root.rglob("*"))
                        if path.is_file() and path.name not in ("reading.json", "launch-status.json")]
    reading["durable_root"] = str(root)
    reading["durable_bytes"] = sum(item["bytes"] for item in reading["files"])
    reading["initial_action_and_reward_identity_all_nine"] = True
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
                      "files": len(result["files"]), "durable_bytes": result["durable_bytes"],
                      "seed_contrasts": result["seed_contrasts"]}))
