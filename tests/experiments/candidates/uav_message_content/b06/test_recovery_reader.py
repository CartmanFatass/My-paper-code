import copy
import hashlib
import json

import pytest

from experiments.candidates.uav_message_content.read_b06_recovery import join_panel, verify_config, verify_evaluation_stream


def rows(master, arm, episodes):
    return [dict(master=master, arm=arm, phase="final_eval", episode=e,
                 reset_seed=1970002000 + e, channel_seed=1970007000 + e,
                 motion_seed=1970003000 + e) for e in episodes]


def test_exact_original_recovery_partition_is_explicit_and_nonmutating():
    original = rows(19703, "D", range(9))
    recovery = rows(19703, "D", range(9, 32))
    snapshot = copy.deepcopy([original, recovery])
    assert len(join_panel(original, recovery, 19703, "D")) == 32
    assert [original, recovery] == snapshot
    assert len(join_panel([], rows(19451, "B40", range(32)), 19451, "B40")) == 32
    assert len(join_panel(rows(19701, "K", range(32)), [], 19701, "K")) == 32


@pytest.mark.parametrize("kind", ["overlap", "missing", "wrong_seed", "wrong_arm", "order", "replaced_original"])
def test_partition_rejects_more_than_a_plausible_total(kind):
    original = rows(19703, "D", range(9))
    recovery = rows(19703, "D", range(9, 32))
    if kind == "overlap":
        recovery[0] = rows(19703, "D", [8])[0]
    elif kind == "missing":
        recovery.pop()
    elif kind == "wrong_seed":
        recovery[0]["motion_seed"] += 1
    elif kind == "wrong_arm":
        recovery[0]["arm"] = "K"
    elif kind == "order":
        recovery.reverse()
    else:
        recovery.insert(0, original.pop())
    with pytest.raises(AssertionError):
        join_panel(original, recovery, 19703, "D")


@pytest.fixture
def evaluation_stream(tmp_path):
    saved = [dict(phase="final_eval", delivered_packets=254, pending_at_end=2)]
    path = tmp_path / "episodes.jsonl"
    path.write_text(json.dumps(saved[0]) + "\n")
    updates = tmp_path / "updates.jsonl"
    updates.write_bytes(b"")
    return dict(directory=str(tmp_path), rows=saved, counts=dict(delivered_packets=254, censored_packets=2),
                episode_stream_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                update_stream_sha256=hashlib.sha256(b"").hexdigest())


def test_recovery_streams_are_required_even_for_partial_d(evaluation_stream):
    assert verify_evaluation_stream(evaluation_stream)["updates"] == 0


@pytest.mark.parametrize("kind", ["missing", "truncated", "row_disagrees", "training", "packet_total", "nonempty_updates"])
def test_recovery_stream_corruption_cannot_pass(evaluation_stream, tmp_path, kind):
    cell = evaluation_stream
    if kind == "missing":
        (tmp_path / "episodes.jsonl").unlink()
    elif kind == "truncated":
        (tmp_path / "episodes.jsonl").write_bytes(b"")
    elif kind == "row_disagrees":
        cell["rows"][0]["extra"] = 1
    elif kind == "training":
        cell["rows"][0]["phase"] = "train"
        path = tmp_path / "episodes.jsonl"
        path.write_text(json.dumps(cell["rows"][0]) + "\n")
        cell["episode_stream_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif kind == "packet_total":
        cell["counts"]["delivered_packets"] -= 1
    else:
        path = tmp_path / "updates.jsonl"
        path.write_text("{}\n")
        cell["update_stream_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises((AssertionError, FileNotFoundError)):
        verify_evaluation_stream(cell)


@pytest.mark.parametrize("change", [None, "digest", "device", "optimizer", "coverage", "seed"])
def test_recovery_configuration_checks_content_and_fixed_semantics(tmp_path, change):
    bound = dict(checkpoint_input={"parent": "bound"}, unfinished_d={"final_checkpoint": {"D": "bound"}},
                 original={"operation": "interrupted"})
    config = dict(seed=19701, launch_sha="recovery-source", horizon=256, dtype="float32", device="cpu",
                  node="local_linux", torch_threads=1, torch_interop_threads=1, blas_threads=1,
                  deployment="sampled_composed_policy", eval_world_base=1970002000,
                  eval_channel_base=1970007000, eval_motion_base=1970003000,
                  d_episodes=list(range(9, 32)), b40_episodes=list(range(32)),
                  parent_checkpoint=bound["checkpoint_input"], d_checkpoint=bound["unfinished_d"]["final_checkpoint"],
                  original=bound["original"], cpu_limit_seconds=600, optimizer_constructed=False, automatic_retry=False)
    if change == "device":
        config["device"] = "cuda"
    elif change == "optimizer":
        config["optimizer_constructed"] = True
    elif change == "coverage":
        config["d_episodes"] = list(range(8, 32))
    elif change == "seed":
        config["seed"] += 1
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    summary = dict(launch_sha="recovery-source", config_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if change == "digest":
        path.write_text(path.read_text() + "\n")
    if change is None:
        assert verify_config(path, summary, bound) == summary["config_sha256"]
    else:
        with pytest.raises(AssertionError):
            verify_config(path, summary, bound)
