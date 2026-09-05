"""Synthetic engineering inputs; no formal learner or empirical residual result."""

import ast
from dataclasses import replace
import inspect
import json
from pathlib import Path
import re
import time

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.residual_cycle_endpoints_b04 import experiment as e
from scripts import run_crto_residual_cycle_endpoints_b04 as runner


def full_fixture():
    toy_train, _, calibration, _ = e.b01._toy_population()
    labels = json.loads((Path(__file__).parents[1] / "raw_cycle_readout_b02" / "native_labels.json").read_text())["rows"]
    train = []
    for i, address in enumerate(a for a in e.b01.SELECTED_ROWS if a.split == "TRAIN"):
        key = e.base.RowKey(address.source_slot, e.base.Split.TRAIN, "K8", address.episode_index, 60, 0)
        train.append(replace(toy_train[0], key=key, target=np.full(8, i / 20, dtype=np.float32)))
    evaluation = []
    for i, label in enumerate(labels):
        rep, split, regime, episode, primitive, agent = label["row_key"].split("/")
        key = e.base.RowKey(int(rep), e.base.Split(split), regime, int(episode), int(primitive), int(agent))
        evaluation.append(replace(toy_train[0], key=key, target=np.full(8, i / 20, dtype=np.float32),
            legal_mask=np.asarray(label["legal_mask"]), g16=np.asarray(label["g16"], dtype=np.float64)))
    return tuple(sorted(train, key=lambda r: r.key.canonical)), tuple(evaluation), calibration, labels


def test_real_packet_geometry_and_split_donor_binding(monkeypatch):
    train, evaluation, calibration, _ = full_fixture()
    calls = []
    original = e.b01.derange_packets
    def derange(*args, **kwargs):
        calls.append(kwargs["split_ordinal"])
        return original(*args, **kwargs)
    monkeypatch.setattr(e.b01, "derange_packets", derange)
    packets, maps = e.packet_sets(train, evaluation, calibration, 0)
    assert calls == [0, 1]
    for split, rows in (("TRAIN", train), ("EVALUATION", evaluation)):
        raw, true, deranged = (packets[split][a] for a in e.ARMS)
        assert not np.array_equal(raw.values, true.values)
        assert np.array_equal(raw.values[:, :8], np.stack([r.target for r in rows]))
        assert np.array_equal(true.values[:, :8], raw.values[:, :8])  # identity factor/zero mean fixture
        assert np.all(true.values[:, 24:] == 0)
        assert np.all(true.values[:, 8:16] >= -1) and np.all(true.values[:, 8:16] <= 1)
        assert np.all(true.values[:, 20:23] == 0)  # adverse-sign negatives of positive coordinates
        by_key = {r.key.text: i for i, r in enumerate(rows)}
        assert set(m["donor"] for m in maps[split]) == set(by_key)
        for mapping in maps[split]:
            recipient, donor = (by_key[mapping[k]] for k in ("recipient", "donor"))
            assert recipient != donor
            assert rows[recipient].derangement_cell == rows[donor].derangement_cell
            assert np.array_equal(deranged.values[recipient], true.values[donor])
            assert deranged.row_keys[recipient] == rows[recipient].key.text
        assert all(p.row_keys == tuple(r.key.text for r in rows) for p in packets[split].values())
    counts = e.exposure_counts(train, maps["TRAIN"], e.ENDPOINTS, 32)
    for budget, expected in (("SHORT", 22), ("LONG", 172)):
        row = counts[budget]
        assert row["recipient_counts_all_arms"] == row["calibrated_derangement_donor_counts"]
        assert set(row["recipient_counts_all_arms"].values()) == {expected}


def test_unchanged_numerical_loop_and_new_caps_movement():
    old, new = inspect.getsource(e.raw.train_raw), inspect.getsource(e.train_path)
    def numerical_prefix(source):
        source = source[source.index("    order ="):source.index("        if update in trace_updates:")]
        source = source.replace("    training_started = time.perf_counter()\n", "")
        return re.sub(r"        check_wall\([^\n]+\)\n", "", source)
    assert numerical_prefix(old) == numerical_prefix(new)
    assert "snapshot = base.deepcopy(model).eval()" in new
    expression = next(n.test for n in ast.walk(ast.parse(new)) if isinstance(n, ast.If)
                      and isinstance(n.test, ast.BoolOp) and "final_update" in ast.unparse(n.test))
    def invalid(update, movement):
        return eval(compile(ast.Expression(expression), "<movement predicate>", "eval"),
                    {"base": e.base, "update": update, "final_update": 258, "movement": movement})
    assert not invalid(33, {"l2": 0., "linf": 0.})
    assert invalid(258, {"l2": 0., "linf": 0.})
    assert invalid(33, {"l2": np.nan, "linf": 1.})
    assert not invalid(258, {"l2": .1, "linf": .2})
    started = time.perf_counter()
    e.check_wall(started - 601, 901)  # previous object caps no longer apply
    with pytest.raises(TimeoutError, match="1500"):
        e.check_wall(started - 1501)
    with pytest.raises(TimeoutError, match="1200"):
        e.check_wall(started, 1201)


@pytest.mark.parametrize("values,competent,branch", [
    (((.008, .001), (.001, .001), (.008, .001)), True, "BR-A — ALIGNED_SHORT_ONLY"),
    (((.008, .004), (.001, 0), (.008, .004)), True, "BR-B — PERSISTENT_ALIGNED_SIGNAL"),
    (((.008, .001), (.001, .001), (.001, .001)), True, "BR-C — GENERIC_PREPROCESSING"),
    (((.001, .001), (.001, .001), (.008, .001)), True, "BR-D — NO_TRUE_GAIN"),
    (((.008, .001), (.001, .001), (.008, .001)), False, "BR-E — COMPARATOR_WEAK"),
    (((.008, .001), (.001, .008), (.008, .001)), True, "BR-F — MIXED_OR_UNRESOLVED"),
])
def test_unchanged_b01_first_matching_rule(values, competent, branch):
    metrics = {arm: {budget: {"equal_side_regret": value,
               "sides": {side: {"row_count": 8, "exact_action_count": 6 if competent else 5,
                                 "mean_regret": .001} for side in ("KEEP", "REPLAN")}}
               for budget, value in zip(e.ENDPOINTS, pair)} for arm, pair in zip(e.ARMS, values)}
    assert e.b01.apply_result_rule(metrics) == branch


def test_full_publication_calibration_donors_six_predictions(tmp_path):
    train, evaluation, calibration, labels = full_fixture()
    packets, maps = e.packet_sets(train, evaluation, calibration, 0)
    predictions = {arm: {u: np.array([[((i + j + k + u) % 13) / 13 for j in range(8)]
                                     for i in range(16)], dtype=np.float32) for u in e.ENDPOINTS.values()}
                   for k, arm in enumerate(e.ARMS)}
    exposure = {arm: [{**e.base._exposure_line(u, e.base.INITIAL_ANCHOR, None), "representation": arm}
                      for u in e.ENDPOINTS.values()] for arm in e.ARMS}
    summary = e.score_summary(labels, predictions, exposure, e.ENDPOINTS)
    summary.update(derangement_donor_maps=maps, endpoint_occurrences=e.exposure_counts(train, maps["TRAIN"], e.ENDPOINTS, 32),
                   calibration={"engineering_only": "synthetic 8-coordinate calibration support", "example_count": 16,
                                "support": calibration.sorted_residuals.tolist()},
                   engineering_only="synthetic packets/calibration/predictions; existing native labels; no learner")
    e.raw.publish_summary(tmp_path, summary)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert len(loaded["derangement_donor_maps"]["TRAIN"]) == 48
    assert len(loaded["derangement_donor_maps"]["EVALUATION"]) == 16
    assert sum(len(m["rows"]) for arm in loaded["representations"].values() for m in arm.values()) == 96
    for arm in e.ARMS:
        for budget, update in e.ENDPOINTS.items():
            point = loaded["representations"][arm][budget]
            assert point["exposure"]["representation"] == arm
            assert point["exposure"]["processed_examples"] == 32 * update
            assert all(v["row_count"] == 8 for v in point["sides"].values())
            assert [r["row_key"] for r in point["rows"]] == [r.key.text for r in evaluation]
    cost = e.project_cost()
    assert cost["projected_shared_seconds"] == pytest.approx(1307.3682797320312)
    assert cost["projection_within_cap"]


def test_one_toy_smoke_three_fresh_paths(tmp_path, monkeypatch, capsys):
    assert e.base.thread_contract()["matches"]
    initial, optimizers, stages, packets_seen = [], [], [], []
    model_class, optimizer_class = e.base.CommonHistoryGate, e.torch.optim.Adam
    original_init, original_train, original_forward = optimizer_class.__init__, e.train_path, e.raw.forward_snapshots
    def model(*args, **kwargs):
        result = model_class(*args, **kwargs)
        initial.append(e.base._parameter_tensors(result))
        return result
    def optimizer_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        assert not self.state
        optimizers.append(self)
    def train(*args, **kwargs):
        packets_seen.append(args[1].values.copy())
        result = original_train(*args, **kwargs)
        stages.append(kwargs["representation"])
        return result
    def forward(*args, **kwargs):
        assert stages[:3] == list(e.ARMS)
        stages.append("forward")
        return original_forward(*args, **kwargs)
    monkeypatch.setattr(e.base, "CommonHistoryGate", model)
    monkeypatch.setattr(optimizer_class, "__init__", optimizer_init)
    monkeypatch.setattr(e, "train_path", train)
    monkeypatch.setattr(e.raw, "forward_snapshots", forward)
    assert runner.main(["run", "--toy", "--output-dir", str(tmp_path), "--execution-node", "local-engineering-smoke"]) == 0
    capsys.readouterr()
    assert len(initial) == len({id(o) for o in optimizers}) == 3
    assert all(e.torch.equal(initial[0][k], state[k]) for state in initial[1:] for k in initial[0])
    assert not np.array_equal(packets_seen[0], packets_seen[1])
    assert not np.array_equal(packets_seen[1], packets_seen[2])
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["result_branch"] is None and summary["resources"]["wall_seconds"] < 60
    assert summary["work_counts"]["gate_updates"] == 18
    assert summary["work_counts"]["network_forward_rows"] == summary["work_counts"]["scored_decisions"] == 36
    assert stages == list(e.ARMS) + ["forward"] * 3
