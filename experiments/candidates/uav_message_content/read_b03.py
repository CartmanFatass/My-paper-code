"""Read the fixed B03 deployment panel without policy or environment calls."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.uav_message_content.read_b02 import (
    behavior_from_observations, close, digest, packet_from_observations,
)


ASSETS = ("C", "B", "O", "L")
CANONICAL_ROOT = Path("/home/wu/projects/HMASD/runs/uav_message_content")
BOUND = {
    "C": (19431, "b01_s19431/C/final.pt", 463293,
          "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"),
    "B": (19451, "b02_preserved_scalar/19451/B/final.pt", 463357,
          "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"),
    "O": (19452, "b02_preserved_scalar/19452/O/final.pt", 463357,
          "90760a722081dec5442aeec85c9302ae3992dcfb96f0bf919aa81389815aa684"),
    "L": (19452, "b02_preserved_scalar/19452/L/final.pt", 464366,
          "c8df7428611608ae0c2786b6b9e395e8183d3b79b30fcdd197e4fcdc9c643f59"),
}
METRICS = ("J_net", "J_physical", "served_users_per_tick", "Q", "charge_per_tick",
           "boundary_fraction", "height_floor_fraction", "height_ceiling_fraction",
           "mean_height_m")
T95_DF31 = 2.0395134463964077


def paired_difference(first, second, metric):
    assert len(first) == len(second) == 32
    assert [row["episode"] for row in first] == list(range(32))
    assert [row["episode"] for row in second] == list(range(32))
    values = [a[metric] - b[metric] for a, b in zip(first, second)]
    assert np.isfinite(values).all()
    mean, sd = statistics.mean(values), statistics.stdev(values)
    half_width = T95_DF31 * sd / np.sqrt(32)
    return dict(mean=mean, sample_sd=sd,
                descriptive_t95_df31=[mean - half_width, mean + half_width],
                minimum=min(values), maximum=max(values),
                positive_worlds=[i for i, value in enumerate(values) if value > 0],
                adverse_worlds=[i for i, value in enumerate(values) if value < 0],
                differences=values)


def choose_asset(rows):
    """Apply the prospective point-mean rule only to a complete, paired panel."""
    assert set(rows) == set(ASSETS)
    for asset in ASSETS:
        assert len(rows[asset]) == 32
        assert [row["episode"] for row in rows[asset]] == list(range(32))
    contrasts = {asset: {metric: paired_difference(rows[asset], rows["C"], metric)
                         for metric in ("J_net", "served_users_per_tick")}
                 for asset in ASSETS[1:]}
    eligible = [asset for asset in ASSETS[1:]
                if all(value["mean"] > 0 for value in contrasts[asset].values())]
    levels = {asset: {metric: statistics.mean(row[metric] for row in rows[asset])
                      for metric in ("J_net", "served_users_per_tick")}
              for asset in ASSETS}
    selected = max(eligible, key=lambda asset: (
        levels[asset]["J_net"], levels[asset]["served_users_per_tick"],
        -ASSETS.index(asset))) if eligible else "C"
    return dict(selected=selected, eligible=eligible, levels=levels,
                versus_C=contrasts, provisional=True, selection_adjusted=False,
                rule="Positive unrounded paired mean J and service versus C; highest J, then service, then C/B/O/L.")


def validate_exposure(cells, actual):
    assert [cell["label"] for cell in cells] == list(ASSETS)
    expected_cells = []
    for cell in cells:
        rows = cell["rows"]
        assert len(rows) == 32 and all(row["steps"] == 256 for row in rows)
        expected = dict(constructors=1, explicit_resets=32, eval_episodes=32,
                        team_steps=8192, native_step_calls=8192, motion_samples=40960,
                        content_samples=8192 if cell["label"] == "L" else 0,
                        broadcasts=8192, attempts=8192, fits=0, optimizer_steps=0,
                        evaluation_optimizer_steps=0, actor_forward_calls=8192,
                        critic_forward_calls=0, diagnostic_forward_calls=0,
                        delivered_packets=sum(row["delivered_packets"] for row in rows),
                        censored_packets=sum(row["pending_at_end"] for row in rows))
        assert expected["delivered_packets"] + expected["censored_packets"] == 8192
        for key, value in expected.items():
            assert cell["counts"][key] == value, (cell["label"], key, cell["counts"][key], value)
        expected_cells.append(expected)
    for key in expected_cells[0]:
        value = sum(expected[key] for expected in expected_cells)
        assert actual[key] == value, ("aggregate", key, actual[key], value)


def read_trace(row, asset):
    path = Path(row["raw"])
    assert digest(path) == row["raw_sha256"]
    shapes = dict(actor_input=(256, 5, 171), pre_tanh_motion=(256, 5, 3),
                  action=(256, 5, 3), packet=(256, 7), pre_tanh_content=(256, 1),
                  records=(256, 5, 5, 10), pending_after_send=(256, 5))
    shapes.update({key: (256,) for key in (
        "due", "good", "deliveries", "reward_physical", "reward_net",
        "served_users", "Q", "sender")})
    with np.load(path, allow_pickle=False) as data:
        assert set(data.files) == set(shapes)
        for key, shape in shapes.items():
            assert data[key].shape == shape, (key, data[key].shape, shape)
            assert np.isfinite(data[key]).all(), key
        obs = data["actor_input"]
        close(obs[:, :, 107], 0, 0)
        close(obs[0, :, 104:107], 0, 0)
        close(obs[1:, :, 104:107], data["action"][:-1], 0)
        close(obs[:, :, 110:115], np.broadcast_to(np.eye(5), (256, 5, 5)), 0)
        pending = np.zeros(5, dtype=bool)
        records = np.zeros((5, 5, 10), dtype=np.float32)
        channel_rng = np.random.default_rng(row["channel_seed"])
        good = bool(channel_rng.integers(2))
        delivered = 0
        for t in range(256):
            assert int(data["good"][t]) == int(good)
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
            close(obs[t, :, 108:110], np.tile(np.eye(2)[int(good)], (5, 1)), 0)
            close(obs[t, :, 115:120], np.tile(np.eye(5)[sender], (5, 1)), 0)
            assert int(data["due"][t]) == t + (1 if good else 5)
            expected = packet_from_observations(obs, t, sender, asset)
            if asset == "L":
                expected[5] = (1 + np.tanh(data["pre_tanh_content"][t, 0])) / 2
            else:
                close(data["pre_tanh_content"][t], 0, 0)
            close(data["packet"][t], expected, 3e-7)
            assert 0 <= float(data["packet"][t, 5]) <= 1
            pending[sender] = True
            close(data["pending_after_send"][t], pending, 0)
            delivered += len(arrived)
            if channel_rng.random() >= .95:
                good = not good
        close(data["action"], np.tanh(data["pre_tanh_motion"]), 1e-6)
        action_hash = hashlib.sha256(data["action"].tobytes()).hexdigest()
        assert action_hash == row["action_sequence_sha256"]
        assert np.all((data["served_users"] >= 0) & (data["served_users"] <= 50))
        close(data["served_users"], np.round(data["served_users"]), 0)
        assert np.all((data["Q"] >= 0) & (data["Q"] <= 1))
        close(data["reward_physical"], .014 * data["served_users"] + .3 * data["Q"])
        close(data["reward_net"], data["reward_physical"] - .001)
        for field, key in (("J_net", "reward_net"), ("J_physical", "reward_physical"),
                           ("served_users_per_tick", "served_users"), ("Q", "Q")):
            close(row[field], data[key].mean())
        close(row["charge_per_tick"], .001)
        assert delivered == row["delivered_packets"]
        censored = int(pending.sum())
        assert censored == row["pending_at_end"] == int((data["due"] >= 256).sum())
        assert delivered + censored == 256
        assert hashlib.sha256(bytes(data["good"].tolist())).hexdigest() == row["channel_sequence_sha256"]
        behavior = behavior_from_observations(obs)
        for key, value in behavior.items():
            close(row[key], value, 2e-5 if key == "mean_height_m" else 1e-7)
        return dict(delivered=delivered, censored=censored,
                    scalar_mean=float(data["packet"][:, 5].mean()),
                    scalar_std=float(data["packet"][:, 5].std()),
                    action_sha256=action_hash,
                    reward_sha256=hashlib.sha256(data["reward_net"].tobytes()).hexdigest(),
                    **{key: float(value) for key, value in behavior.items()})


def read_run(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    manifest = json.loads((root / "launch-manifest.json").read_text())
    witness = json.loads((root / "process-exit.json").read_text())
    assert summary["status"] == "COMPLETE" and summary["seed"] == 19461
    assert summary["source_sha"] == manifest["sha"]
    assert manifest["node"] == "wsl_4070" and manifest["direction"] == "uav_message_content"
    assert manifest["lead"] == "Codex DM (native child)"
    assert witness["exit_code"] == 0
    assert [item["label"] for item in summary["assets"]] == list(ASSETS)
    rows_by_asset, levels, raw_checks, frozen_assets = {}, {}, {}, {}
    for cell in summary["assets"]:
        asset = cell["label"]
        master, relative, size, sha = BOUND[asset]
        canonical = CANONICAL_ROOT / relative
        assert canonical.stat().st_size == size and digest(canonical) == sha
        assert cell["source"]["sha256"] == sha and cell["source"]["bytes"] == size
        assert cell["master"] == master and cell["status"] == "COMPLETE"
        assert cell["initial_actor_sha256"] == cell["final_actor_sha256"]
        rows = [json.loads(line) for line in (Path(cell["directory"]) / "episodes.jsonl").read_text().splitlines()]
        assert rows == cell["rows"] and len(rows) == 32
        assert [row["episode"] for row in rows] == list(range(32))
        for e, row in enumerate(rows):
            assert row["asset"] == asset and row["master"] == master and row["phase"] == "eval"
            assert row["checkpoint_sha256"] == sha
            for key, start in (("reset_seed", 1946102000), ("channel_seed", 1946107000),
                               ("motion_seed", 1946103000), ("content_seed", 1946104000)):
                assert row[key] == start + e
            assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
            assert row["collided_attempts"] == 0
        rows_by_asset[asset] = rows
        levels[asset] = {key: statistics.mean(row[key] for row in rows) for key in METRICS}
        raw_checks[asset] = [read_trace(row, asset) for row in rows]
        frozen_assets[asset] = dict(canonical_path=str(canonical), sha256=sha, bytes=size,
                                    actor_tensor_sha256=cell["initial_actor_sha256"])
    for asset in ASSETS[1:]:
        for reference, row in zip(rows_by_asset["C"], rows_by_asset[asset]):
            for key in ("reset_seed", "channel_seed", "motion_seed", "content_seed",
                        "initial_scene_sha256", "channel_sequence_sha256"):
                assert row[key] == reference[key], (asset, key)
    validate_exposure(summary["assets"], summary["actual"])
    assert summary["resources"]["torch_threads"] == 1
    assert summary["resources"]["torch_interop_threads"] == 1
    contrasts = {f"{first}-{second}": {
        metric: paired_difference(rows_by_asset[first], rows_by_asset[second], metric)
        for metric in METRICS}
        for second, first in itertools.combinations(ASSETS, 2)}
    files = [dict(path=str(path.relative_to(root)), bytes=path.stat().st_size, sha256=digest(path))
             for path in sorted(root.rglob("*")) if path.is_file()
             and path.name not in ("reading.json", "launch-status.json")]
    return dict(all_checks_passed=True, source_sha=summary["source_sha"],
                summary_sha256=digest(root / "summary.json"), reader_sha256=digest(__file__),
                native_steps_added=0, optimizer_calls_added=0, model_or_policy_calls_added=0,
                levels=levels, contrasts=contrasts, selection=choose_asset(rows_by_asset),
                frozen_assets=frozen_assets, raw_checks=raw_checks,
                actual=summary["actual"], resources=summary["resources"],
                files=files, durable_root=str(root), durable_bytes=sum(item["bytes"] for item in files),
                limitations=[
                    "Four selected paid assets, not independent training replications or recipe recurrence.",
                    "World/protocol replicates are deployment samples conditional on the selected checkpoints.",
                    "Point-mean reuse choice and nominal df31 intervals are not selection-adjusted confirmation.",
                    "Complete-package comparisons do not identify scalar semantics or causal effect of preserving C.",
                    "Pre-action boundary/height readings are behavior, not energy or physical safety.",
                    "All B01/B02 selection exposure and adverse continuations remain part of the evidence."])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    reading = read_run(args.run)
    args.output.write_text(json.dumps(reading, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: reading[key] for key in ("all_checks_passed", "levels", "selection", "durable_bytes")}))
