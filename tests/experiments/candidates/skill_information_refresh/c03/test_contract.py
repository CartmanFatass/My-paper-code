from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.skill_information_refresh.c01.host import (
    APPROACH, BYPASS, CROSSING, DONE, SHARED, CrossingHost, LocalView, Worlds,
)
from experiments.candidates.skill_information_refresh.c01.learner import (
    build_scheduler, collect as original_collect, flat_parameters,
)
from experiments.candidates.skill_information_refresh.c03.study import (
    CHECKPOINTS, Config, collect, load_frozen, paired, release_due, run_study,
    stale_release_waits,
)


def legal_release_view():
    own = np.tile([DONE, 0, 0, 4, SHARED], (8, 1))
    last = np.tile([APPROACH, 4, 0, 12, SHARED], (8, 1))
    return LocalView(8, 96, 0, own, last, np.zeros(8, dtype=np.int16),
        np.zeros((8, 5), dtype=np.int16), np.zeros(8, dtype=bool),
        np.full(8, 9), np.ones(8, dtype=bool))


def test_release_guard_truth_cases_and_no_peer_information():
    view = legal_release_view()
    assert release_due(view).all()
    own, last, times = view.own.copy(), view.last_sent.copy(), view.last_sent_time.copy()
    own[1, 0] = APPROACH
    last[2, 0] = DONE
    times[3] = -1
    last[4, 3] = 8  # The last commitment is expired, not a valid stale block.
    last[5, 4] = BYPASS
    last[6, 1] = 8  # Projected distance 2 is outside the stale yielding range.
    last[7, 0] = CROSSING
    changed = replace(view, own=own, last_sent=last, last_sent_time=times)
    assert release_due(changed).tolist() == [True, False, False, False, False, False, False, False]
    unrelated = replace(changed, peer=np.full((8, 5), 99), peer_valid=np.ones(8, dtype=bool),
        peer_age=np.zeros(8), available=np.zeros(8, dtype=bool))
    assert np.array_equal(release_due(changed), release_due(unrelated))


@pytest.mark.parametrize("arm", ["LEARNED", "AGE_CHANGE", "PRE_DECISION", "POLL"])
def test_unguarded_collector_replays_original_semantics(arm):
    torch.set_num_threads(1)
    model = build_scheduler(17)
    worlds = Worlds.make(19, 0, range(4), 48)
    rows, trace = collect(CrossingHost(worlds), arm=arm,
        model=model if arm == "LEARNED" else None, retain_trace=True)
    original_rows, _, original_trace = original_collect(CrossingHost(worlds), arm=arm,
        model=model if arm == "LEARNED" else None, retain_trace=True)
    for old, new in zip(original_rows, rows):
        assert old == {key: new[key] for key in old}
    for key in original_trace:
        assert np.array_equal(original_trace[key], trace[key]), key


def test_guarded_collect_retains_quota_masks_and_loaded_parameters():
    torch.set_num_threads(1)
    model = build_scheduler(31)
    before = flat_parameters(model)
    rows, trace = collect(CrossingHost(Worlds.make(29, 0, range(8), 96)),
        model=model, release=True, retain_trace=True)
    sent = trace["sent"].reshape(8, 12, 8)
    assert (sent[:, :, ::2].sum(2) == 1).all()
    assert (sent[:, :, 1::2].sum(2) == 1).all()
    assert all(row["packets"] == 24 and row["bytes"] == 192 for row in rows)
    assert (trace["requested"] == (trace["raw_requested"] | trace["release_due"])).all()
    forced = np.arange(96) % 8 >= 6
    expected_overrides = trace["release_due"] & ~trace["raw_requested"] & trace["choice_mask"]
    assert all(row["release_overrides"] == int(expected_overrides[i].sum()) for i, row in enumerate(rows))
    assert not trace["choice_mask"][:, forced].any()
    assert torch.equal(before, flat_parameters(model))


def waiting_host():
    host = CrossingHost(Worlds.make(11, 0, [0], 48))
    host.t = 8
    host.stage[0] = [DONE, APPROACH]
    host.distance[0] = [0, 0]
    host.route[0] = [SHARED, SHARED]
    host.last_sent[0, 0] = [APPROACH, 4, 0, 12, SHARED]
    host.last_sent_time[0, 0] = 0
    host.cache[0, 1] = host.last_sent[0, 0]
    host.cache_time[0, 1] = 0
    return host


def test_release_intervenes_at_next_delivery_without_free_extra_packet():
    host = waiting_host()
    assert stale_release_waits(host).tolist() == [1]
    assert release_due(host.view()).tolist() == [True]
    host.step(release_due(host.view()))
    assert host.metrics["packets"].tolist() == [1]
    assert host.spent[0, 0]
    assert host.cache[0, 1, 0] == DONE  # One tick later, before robot 1's next feedback.
    assert stale_release_waits(host).tolist() == [0]
    unavailable = waiting_host()
    unavailable.spent[0, 0] = True
    unavailable.step(release_due(unavailable.view()))
    assert unavailable.metrics["packets"].tolist() == [0]
    assert stale_release_waits(unavailable).tolist() == [1]


def make_checkpoints(root):
    specs = []
    for spec in CHECKPOINTS:
        path = root / spec.path
        path.parent.mkdir(parents=True, exist_ok=True)
        config = dict(seed=spec.seed, horizon=96, train_episodes=4096,
            initial_episodes=64, selection_episodes=256, final_episodes=256, batch=32, epochs=4)
        # Synthetic untrained fixtures, never scientific evidence or result inputs.
        torch.save(dict(model=build_scheduler(spec.seed).state_dict(),
            launch_sha=spec.source_sha, config=config), path)
        specs.append(replace(spec, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(specs)


def test_checkpoint_digest_metadata_and_readonly_model(tmp_path):
    torch.set_num_threads(1)
    specs = make_checkpoints(tmp_path)
    model = load_frozen(tmp_path, specs[0])
    assert not model.training
    assert not any(p.requires_grad for p in model.parameters())
    with pytest.raises(ValueError, match="digest"):
        load_frozen(tmp_path, replace(specs[0], sha256="0" * 64))
    with pytest.raises(ValueError, match="metadata"):
        load_frozen(tmp_path, replace(specs[0], seed=123))


def test_complete_fixture_counts_selection_pairs_and_no_updates(tmp_path):
    torch.set_num_threads(1)
    specs = make_checkpoints(tmp_path)
    out = tmp_path / "output"
    config = Config(seed=71, horizon=48, selection_episodes=2, final_episodes=3, batch=2)
    result = run_study(out, "a" * 40, tmp_path, config, specs)
    assert result["status"] == "COMPLETE"
    counts = result["counts"]
    assert counts["started_fits"] == counts["optimizer_steps"] == counts["train_transitions"] == 0
    assert counts["evaluation_optimizer_steps"] == 0
    assert counts["selection_episodes"] == 36 and counts["eval_episodes"] == 30
    assert counts["selection_transitions"] == 36 * 48 and counts["eval_transitions"] == 30 * 48
    assert len(result["selection"]) == 18 and len(result["final"]) == 10
    assert len(result["release_effect"]) == 3 and len(result["versus_selected_simple"]) == 6
    assert (out / "updates.jsonl").read_text() == ""
    assert all(value["displacement_from_loaded"] == 0 for value in result["frozen_parameters"].values())
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(rows) == 66
    for name, contrast in result["release_effect"].items():
        left = [r for r in rows if r["phase"] == "eval" and r["arm"] == name + "_RELEASE"]
        right = [r for r in rows if r["phase"] == "eval" and r["arm"] == name]
        assert contrast == paired(left, right)
        assert np.array_equal(np.load(out / f"final_trace_{name}.npz")["world_ids"], np.arange(3))
    best = sorted(result["selection"], key=lambda r: (-r["reading"]["service"], r["family"], r["variant"]))[0]
    assert result["selected_simple_reference"] == best["family"]
    with pytest.raises(FileExistsError):
        run_study(out, "a" * 40, tmp_path, config, specs)


def test_failed_checkpoint_retains_technical_failure_not_negative_result(tmp_path):
    specs = make_checkpoints(tmp_path)
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="digest"):
        run_study(out, "a" * 40, tmp_path, Config(selection_episodes=1, final_episodes=1),
            (replace(specs[0], sha256="0" * 64),))
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "TECHNICAL_FAILURE"
    assert result["counts"]["started_fits"] == result["counts"]["eval_transitions"] == 0
    assert result["final"] == {}


def test_pairs_reject_different_world_order():
    with pytest.raises(ValueError, match="worlds"):
        paired([dict(world_id=1, service=0)], [dict(world_id=2, service=0)])


def test_cli_refuses_unadmitted_execution_before_outputs(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "unadmitted"
    result = subprocess.run([sys.executable, str(root / "scripts/run_sir_c03.py"),
        "--out", str(out), "--launch-sha", "a" * 40], cwd=root,
        capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()
