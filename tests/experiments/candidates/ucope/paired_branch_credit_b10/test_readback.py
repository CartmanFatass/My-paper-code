"""Offline reading rules on handwritten arrays; no training or environment."""
import hashlib
import copy

import numpy as np
import pytest
import torch

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
                means=np.arctanh(context[..., 107:110]).astype(np.float32),
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


def test_commands_and_context_cannot_jointly_override_recorded_mean(tmp_path):
    path = tmp_path / "panel.npz"
    arrays = _arrays(ordinary=True)
    arrays["means"][0, 2, 0, 1] += .1
    np.savez_compressed(path, **arrays)
    with pytest.raises(ValueError, match="tanh of recorded means"):
        readback.panel_reading(path, horizon=4, worlds=2, ordinary=True)
    arrays = _arrays()
    arrays["gate_uniforms"][0, 0, 0] = 1  # Reset hides the wrong coin from the action law.
    np.savez_compressed(path, **arrays)
    with pytest.raises(ValueError, match="invalid gate uniforms"):
        readback.panel_reading(path, horizon=4, worlds=2, ordinary=False)


def test_uniform_addresses_replay_private_draws_without_global_rng_mutation():
    state = torch.get_rng_state().clone()
    for shape in ((256, 5), (2,)):
        stored = torch.rand(shape, generator=torch.Generator().manual_seed(897150000)).numpy()
        readback.verify_uniforms(stored, seed=897150000, shape=shape)
        with pytest.raises(ValueError, match="seed address"):
            readback.verify_uniforms(stored, seed=897150001, shape=shape)
        stored.flat[0] = -0.01
        with pytest.raises(ValueError, match="invalid stored uniform"):
            readback.verify_uniforms(stored, seed=897150000, shape=shape)
    assert torch.equal(state, torch.get_rng_state())


@pytest.mark.parametrize("raw", [{"horizon": 257, "team_steps": 514},
                                 {"horizon": 256, "team_steps": 514}])
def test_raw_pair_exposure_is_bound_before_accepting_its_metadata(tmp_path, monkeypatch, raw):
    monkeypatch.setattr(readback, "inspect_pair", lambda path: raw)
    with pytest.raises(ValueError, match="raw pair exposure"):
        readback.read_scheduled_pair(tmp_path / "pair.npz", common_seed=1, focal_seed=2)


def test_terminal_witness_cannot_be_transplanted_between_same_source_blocks():
    def records(master):
        runner = {"pid": master, "start_ticks": 123, "boot_id": "fixture", "session_id": master + 1}
        supervisor = {"pid": master + 1, "start_ticks": 122, "boot_id": "fixture", "session_id": master + 1}
        output = f"/fixture/runs/ucope/paired_branch_credit_b10_{master}"
        command = ["/fixture/python", "/fixture/source/scripts/run_ucope_paired_branch_credit_b10.py",
                   "--master", str(master), "--out", output, "--launch-sha", readback.SOURCE]
        digest = readback.command_digest(command[0], command[1], command[2:])
        manifest = {"command": command, "source_root": "/fixture/source", "output_root": output,
                    "sha": readback.SOURCE, "direction": "ucope", "command_sha256": digest,
                    "runner_process": {"identity": runner, "pid": master, "supervisor_pid": master + 1},
                    "process": {"identity": supervisor, "pid": master + 1}}
        terminal = {"process_identity": runner, "supervisor_identity": supervisor, "pid": master}
        admission = {"sha": readback.SOURCE, "direction": "ucope", "command_sha256": digest,
                     "child_pid": master, "parent_pid": master + 1}
        return manifest, terminal, admission
    first, second = records(8971), records(8972)
    readback.verify_native_identity(*first, 8971)
    with pytest.raises(ValueError, match="another block"):
        readback.verify_native_identity(second[0], second[1], first[2], 8971)
    with pytest.raises(ValueError, match="admission command"):
        readback.verify_native_identity(second[0], second[1], first[2], 8972)
    terminal = copy.deepcopy(first[1])
    terminal["supervisor_identity"]["start_ticks"] += 1
    with pytest.raises(ValueError, match="terminal process"):
        readback.verify_native_identity(first[0], terminal, first[2], 8971)
