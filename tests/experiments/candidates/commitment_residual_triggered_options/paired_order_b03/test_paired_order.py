"""Non-result checks: synthetic packets/predictions and one toy learner smoke."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.paired_order_b03 import experiment as e
from scripts import run_crto_paired_order_b03 as runner


def formal_order_fixture():
    rows, metadata = [], {}
    for address in e.base.SELECTED_ROWS:
        if address.split != "TRAIN":
            continue
        key = e.base.RowKey(address.source_slot, e.base.Split.TRAIN, "K8", address.episode_index, 60, 0)
        rows.append(SimpleNamespace(key=key))
        metadata[key.text] = address.__dict__.copy()
    rows = tuple(sorted(rows, key=lambda r: r.key.canonical))
    packets = e.base.PacketDataset(tuple(r.key.text for r in rows),
                                  np.repeat(np.arange(48, dtype=np.float32)[:, None], 52, axis=1))
    return rows, packets, metadata


def test_original_pairs_packet_binding_balanced_batches_and_exact_multisets():
    rows, packets, metadata = formal_order_fixture()
    orders, sequences = e.training_orders(rows, packets, metadata)
    paired_rows, paired_packets = orders["PAIRED"]
    expected_pair_indices = [i // 2 for i in range(0, 64, 2) if e.base.SELECTED_ROWS[i].split == "TRAIN"]
    assert len(expected_pair_indices) == 24
    assert [r["original_pair_index"] for r in sequences["PAIRED"]][::2] == expected_pair_indices
    for i in range(0, 48, 2):
        keep, replan = sequences["PAIRED"][i:i + 2]
        declaration_offset = 2 * keep["original_pair_index"]
        assert keep["address"] == e.base.SELECTED_ROWS[declaration_offset].__dict__
        assert replan["address"] == e.base.SELECTED_ROWS[declaration_offset + 1].__dict__
        assert keep["KEEP_address"] == replan["KEEP_address"] == keep["address"]
        assert keep["REPLAN_address"] == replan["REPLAN_address"] == replan["address"]
    for i, row in enumerate(paired_rows):
        canonical_index = sequences["PAIRED"][i]["canonical_index"]
        assert row is rows[canonical_index]
        assert paired_packets.row_keys[i] == packets.row_keys[canonical_index]
        assert np.array_equal(paired_packets.values[i], packets.values[canonical_index])
    assert not np.array_equal(paired_packets.values, packets.values)
    with pytest.raises(ValueError, match="row-key order"):
        packets.require_rows(paired_rows)
    cyclic = np.resize(np.arange(48), 258 * 32)
    for batch in cyclic.reshape(-1, 32):
        members = [sequences["PAIRED"][i] for i in batch]
        assert sum(r["address"]["side"] == "KEEP" for r in members) == 16
        assert sum(r["address"]["side"] == "REPLAN" for r in members) == 16
        assert all(members[i]["original_pair_index"] == members[i + 1]["original_pair_index"]
                   for i in range(0, 32, 2))
    for update, count in ((252, 168), (255, 170), (258, 172)):
        canonical = e.occurrence_counts(rows, update, 32)
        paired = e.occurrence_counts(paired_rows, update, 32)
        assert canonical == paired
        assert set(canonical.values()) == {count}
        assert sum(canonical.values()) == update * 32


@pytest.mark.parametrize("d,canonical,paired,branch", [
    ({252: -.1, 255: 0, 258: .1}, False, False, "B03-COMPARATOR-WEAK"),
    ({252: -.0025001, 255: 0, 258: .1}, True, True, "B03-MATERIAL-REGRET-LOSS"),
    ({252: -.0025, 255: 0, 258: .0025001}, True, True, "B03-PAIRED-ORDER-SIGNAL"),
    ({252: .1, 255: 0, 258: .0025}, True, True, "B03-PAIRED-ORDER-NO-MATERIAL-GAIN"),
    ({252: -.0025, 255: 0, 258: .1}, True, False, "B03-PAIRED-ORDER-INCOMPETENT"),
])
def test_first_matching_rule_and_primary_endpoint(d, canonical, paired, branch):
    assert e.apply_result_rule(d, canonical, paired) == branch


def test_six_formal_size_publications_with_synthetic_predictions(tmp_path):
    labels_path = Path(__file__).parents[1] / "raw_cycle_readout_b02" / "native_labels.json"
    labels = json.loads(labels_path.read_text())["rows"]
    rows, packets, metadata = formal_order_fixture()
    orders, sequences = e.training_orders(rows, packets, metadata)
    predictions = {a: {u: np.array([[((i + j * 3 + u + k) % 7) / 7 for j in range(8)]
                                   for i in range(16)], dtype=np.float32) for u in e.ENDPOINTS}
                   for k, a in enumerate(e.ARMS)}
    exposures = {a: [e.base._exposure_line(u, e.base.INITIAL_ANCHOR, None) for u in e.ENDPOINTS]
                 for a in e.ARMS}
    summary = e.comparison_summary(labels, predictions, exposures, orders)
    summary.update(train_orders=sequences, engineering_only="synthetic predictions and packets; existing native labels")
    e.raw.publish_summary(tmp_path, summary)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert sum(len(point["rows"]) for arm in loaded["arms"].values()
               for point in arm["endpoints"].values()) == 96
    for arm in e.ARMS:
        for update in e.ENDPOINTS:
            point = loaded["arms"][arm]["endpoints"][str(update)]
            assert all(s["row_count"] == 8 for s in point["sides"].values())
            for row in point["rows"]:
                assert row["native_regret"] == max(row["legal_g16"].values()) - row["selected_g16"]
            assert point["exposure"]["processed_examples"] == update * 32
    assert loaded["primary_D"] == loaded["paired_differences"]["258"]
    cost = e.project_cost()
    assert cost["projected_arm_seconds"] == pytest.approx(259.728466544, abs=1e-8)
    assert cost["projected_shared_seconds"] == pytest.approx(302.796226686, abs=1e-8)
    assert cost["prospective_work_counts"]["raw_processed_examples"] == 16512


def test_one_toy_smoke_two_fresh_models_and_optimizers(tmp_path, monkeypatch, capsys):
    models, optimizers, initial, stages, starts = [], [], [], [], []
    original_model, optimizer_class = e.base.CommonHistoryGate, e.base.torch.optim.Adam
    original_optimizer_init = optimizer_class.__init__
    original_train, original_forward = e.raw.train_raw, e.raw.forward_snapshots
    def model(*args, **kwargs):
        result = original_model(*args, **kwargs)
        models.append(result)
        initial.append(e.base._parameter_tensors(result))
        return result
    def optimizer_init(self, *args, **kwargs):
        original_optimizer_init(self, *args, **kwargs)
        optimizers.append(self)
        assert len(self.state) == 0
    def train(*args, **kwargs):
        starts.append(kwargs["started"])
        result = original_train(*args, **kwargs)
        stages.append("train")
        return result
    def forward(*args, **kwargs):
        assert stages[:2] == ["train", "train"]
        stages.append("forward")
        return original_forward(*args, **kwargs)
    monkeypatch.setattr(e.base, "CommonHistoryGate", model)
    monkeypatch.setattr(optimizer_class, "__init__", optimizer_init)
    monkeypatch.setattr(e.raw, "train_raw", train)
    monkeypatch.setattr(e.raw, "forward_snapshots", forward)
    assert runner.main(["run", "--toy", "--output-dir", str(tmp_path), "--execution-node", "local-engineering-smoke"]) == 0
    capsys.readouterr()
    assert stages == ["train", "train", "forward", "forward"]
    assert len(models) == len(optimizers) == 2
    assert models[0] is not models[1] and optimizers[0] is not optimizers[1]
    assert all(e.base.torch.equal(initial[0][k], initial[1][k]) for k in initial[0])
    assert starts[0] == starts[1]
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["result_branch"] is None
    assert summary["resources"]["wall_seconds"] < 60
    assert summary["work_counts"]["raw_gate_updates"] == 18
    assert summary["work_counts"]["network_forward_rows"] == summary["work_counts"]["scored_decisions"] == 36
