"""Offline reading rules on handwritten arrays; no training or environment."""
import hashlib

import numpy as np
import pytest

from experiments.candidates.ucope.paired_branch_credit_b10 import readback


def _arrays(ordinary=False):
    shape = (2, 4, 5)
    coins = np.linspace(0, 1, 40, endpoint=False, dtype=np.float32).reshape(shape)
    probability = np.full(shape, 0.5, np.float32)
    eligible, keep = np.zeros(shape, bool), np.zeros(shape, bool)
    previous = np.zeros(shape + (3,), np.float32)
    commands = np.zeros_like(previous)
    context = np.zeros(shape + (175,), np.float32)
    if ordinary:
        coins.fill(0)
        probability.fill(0)
    for tick in range(4):
        if tick:
            previous[:, tick] = commands[:, tick - 1]
            if not ordinary:
                eligible[:, tick] = ~keep[:, tick - 1]
        keep[:, tick] = eligible[:, tick] & (coins[:, tick] < probability[:, tick])
        fresh = np.full((2, 5, 3), (tick + 1) / 10, np.float32)
        context[:, tick, :, 104:107] = previous[:, tick]
        context[:, tick, :, 107:110] = fresh
        commands[:, tick] = np.where(keep[:, tick, :, None], previous[:, tick], fresh)
    return dict(reward=np.asarray([[.1, .2, .3, .4], [.4, .3, .2, .1]], np.float64),
                commands=commands, previous=previous, context=context, eligible=eligible, keep=keep,
                keep_probability=probability, gate_uniforms=coins)


def test_panel_reader_reconstructs_returns_and_enforces_actual_command_law(tmp_path):
    path = tmp_path / "panel.npz"
    arrays = _arrays()
    np.savez_compressed(path, **arrays)
    result, coins = readback.panel_reading(path, horizon=4, worlds=2, ordinary=False)
    assert result["J"] == pytest.approx([.25, .25])
    assert result["kept"] == 10 and result["eligible"] == 25
    assert result["keep_probability_sd"] == 0
    np.testing.assert_array_equal(coins, arrays["gate_uniforms"])
    arrays["gate_uniforms"][1, 1, 0] = 0
    np.savez_compressed(path, **arrays)
    with pytest.raises(ValueError, match="coins were not applied"):
        readback.panel_reading(path, horizon=4, worlds=2, ordinary=False)


def test_ordinary_panel_cannot_silently_include_a_gating_intervention(tmp_path):
    path = tmp_path / "ordinary.npz"
    np.savez_compressed(path, **_arrays(ordinary=True))
    result, _ = readback.panel_reading(path, horizon=4, worlds=2, ordinary=True)
    assert result["kept"] == result["eligible"] == 0 and result["keep_probability_sd"] is None
    np.savez_compressed(path, **_arrays())
    with pytest.raises(ValueError, match="G acquired"):
        readback.panel_reading(path, horizon=4, worlds=2, ordinary=True)


def test_block_rule_requires_every_declared_seed_even_when_overall_mean_passes():
    blocks = [{"master": master, "comparisons": {left + "_minus_" + right: {"mean": value}
               for left, right in readback.COMPARISONS}}
              for master, value in zip(readback.MASTERS, (.03, .012, .0005))]
    assert readback.investment_reading(blocks)["prefer_paired_over_simple"]
    blocks[2]["comparisons"]["R_CF_minus_G"]["mean"] = -.0005
    result = readback.investment_reading(blocks)
    assert result["R_CF_minus_G"]["three_block_mean"] > .01
    assert not result["retain_paired_over_rich_and_G"]
    with pytest.raises(ValueError, match="exactly the three"):
        readback.investment_reading([blocks[0], blocks[0], blocks[2]])


def test_recorded_size_does_not_substitute_for_artifact_digest(tmp_path):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"abc")
    identity = {"bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()}
    readback.verify_file(path, identity)
    path.write_bytes(b"abd")
    with pytest.raises(ValueError, match="artifact identity mismatch"):
        readback.verify_file(path, identity)
