import hashlib
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel
from experiments.candidates.uav_message_content.read_b03 import (
    ASSETS, choose_asset, paired_difference, read_trace, validate_exposure,
)


def panel(levels):
    return {asset: [dict(episode=e, J_net=levels[asset][0], served_users_per_tick=levels[asset][1])
                    for e in range(32)] for asset in ASSETS}


def test_direct_reader_cli_has_no_pythonpath_dependency():
    root = Path(__file__).resolve().parents[4]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(root / "experiments/candidates/uav_message_content/read_b03.py"), "--help"],
        cwd=root, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "--run" in result.stdout and "--output" in result.stdout


@pytest.mark.parametrize("levels,selected,eligible", [
    ({"C": (.2, 10), "B": (.2, 11), "O": (.3, 9), "L": (.1, 12)}, "C", []),
    ({"C": (.2, 10), "B": (.3, 11), "O": (.4, 10.5), "L": (.35, 12)}, "O", ["B", "O", "L"]),
    ({"C": (.2, 10), "B": (.3, 11), "O": (.3, 12), "L": (.3, 12)}, "O", ["B", "O", "L"]),
    ({"C": (.2, 10), "B": (.3, 11), "O": (.3, 11), "L": (.4, 9)}, "B", ["B", "O"]),
    ({"C": (.2, 10), "B": (.3, 11), "O": (.3, 12), "L": (.30000000000001, 10.1)}, "L", ["B", "O", "L"]),
])
def test_fixed_rule_joint_gain_unrounded_ranking_and_ties(levels, selected, eligible):
    result = choose_asset(panel(levels))
    assert result["selected"] == selected and result["eligible"] == eligible
    assert result["provisional"] and not result["selection_adjusted"]


def test_incomplete_or_reordered_panel_cannot_select():
    rows = panel({asset: (.2, 10) for asset in ASSETS})
    del rows["L"][-1]
    with pytest.raises(AssertionError):
        choose_asset(rows)
    rows = panel({asset: (.2, 10) for asset in ASSETS})
    rows["O"].reverse()
    with pytest.raises(AssertionError):
        choose_asset(rows)


def test_paired_df31_uncertainty_keeps_adverse_worlds():
    first = [dict(episode=e, J_net=e - 15.5) for e in range(32)]
    second = [dict(episode=e, J_net=0.) for e in range(32)]
    result = paired_difference(first, second, "J_net")
    assert result["mean"] == 0
    assert result["adverse_worlds"] == list(range(16))
    assert result["positive_worlds"] == list(range(16, 32))
    # For the integers 0..31, the sample variance is 88 and variance of the mean is 2.75.
    assert result["descriptive_t95_df31"][0] == pytest.approx(-2.0395134463964077 * np.sqrt(2.75))


@pytest.mark.parametrize("scope,key", [
    ("cell", "optimizer_steps"), ("aggregate", "team_steps"),
    ("cell", "diagnostic_forward_calls"), ("aggregate", "critic_forward_calls"),
    ("cell", "content_samples"), ("aggregate", "actor_forward_calls"),
    ("cell", "delivered_packets"), ("aggregate", "motion_samples"),
])
def test_exposure_requires_zero_updates_and_exact_raw_reconciled_counts(scope, key):
    cells = []
    for asset in ASSETS:
        counts = dict(constructors=1, explicit_resets=32, eval_episodes=32,
                      team_steps=8192, native_step_calls=8192, motion_samples=40960,
                      content_samples=8192 if asset == "L" else 0,
                      broadcasts=8192, attempts=8192, fits=0, optimizer_steps=0,
                      evaluation_optimizer_steps=0, actor_forward_calls=8192,
                      critic_forward_calls=0, diagnostic_forward_calls=0,
                      delivered_packets=8128, censored_packets=64)
        rows = [dict(steps=256, delivered_packets=254, pending_at_end=2) for _ in range(32)]
        cells.append(dict(label=asset, counts=counts, rows=rows))
    actual = {key: sum(cell["counts"][key] for cell in cells) for key in cells[0]["counts"]}
    validate_exposure(cells, actual)
    (cells[3]["counts"] if scope == "cell" else actual)[key] += 1
    with pytest.raises(AssertionError):
        validate_exposure(cells, actual)


@pytest.mark.parametrize("asset", ASSETS)
def test_raw_reconstruction_without_environment_or_model(tmp_path, asset):
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = .5
    raw[:, 3:9] = (-.2, 0, .4, .2, 0, .4)
    scalar = {"C": 0., "B": 0., "O": np.sqrt(.08), "L": .7}[asset]
    pre_content = np.array([np.arctanh(2 * scalar - 1) if asset == "L" else 0], dtype=np.float32)
    packet = np.array([.5, .5, .5, .5, .5, scalar, .1], dtype=np.float32)
    channel = Channel(1946107000)
    trace = {name: [] for name in (
        "actor_input", "pre_tanh_motion", "action", "packet", "pre_tanh_content", "due", "good",
        "deliveries", "reward_physical", "reward_net", "served_users", "Q", "records",
        "pending_after_send", "sender")}
    for t in range(256):
        before = channel.delivered
        channel.begin_tick()
        obs = np.concatenate((raw, np.zeros((5, 4), dtype=np.float32), channel.features()), axis=1)
        good, sender = int(channel.good), t % 5
        due = t + (1 if good else 5)
        assert not channel.pending[sender]
        channel.inflight.append((sender, t, due, packet.copy()))
        channel.pending[sender] = True
        values = (obs, np.zeros((5, 3), dtype=np.float32), np.zeros((5, 3), dtype=np.float32),
                  packet.copy(), pre_content.copy(), due, good, channel.delivered - before,
                  .13, .129, 5, .2, channel.records.copy(), channel.pending.copy(), sender)
        for key, value in zip(trace, values):
            trace[key].append(value)
        channel.advance()
    arrays = {key: np.asarray(value) for key, value in trace.items()}
    path = tmp_path / "synthetic.npz"
    np.savez_compressed(path, **arrays)
    row = dict(raw=str(path), raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               channel_seed=1946107000, J_net=.129, J_physical=.13,
               served_users_per_tick=5, Q=.2, charge_per_tick=.001,
               delivered_packets=channel.delivered, pending_at_end=int(channel.pending.sum()),
               channel_sequence_sha256=hashlib.sha256(bytes(arrays["good"].tolist())).hexdigest(),
               action_sequence_sha256=hashlib.sha256(arrays["action"].tobytes()).hexdigest(),
               boundary_fraction=0., height_floor_fraction=0., height_ceiling_fraction=0., mean_height_m=100.)
    result = read_trace(row, asset)
    assert result["delivered"] + result["censored"] == 256
    row["channel_seed"] += 1
    with pytest.raises(AssertionError):
        read_trace(row, asset)
    row["channel_seed"] -= 1
    arrays["packet"][-1, 6] += .05
    np.savez_compressed(path, **arrays)
    row["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(AssertionError):
        read_trace(row, asset)
