"""Budget/default propagation and publication with synthetic observations only."""

import json

from experiments.candidates.ucope.shared_data_return_model_b02 import model as m
from scripts import run_ucope_shared_data_return_model_b02 as b02
from scripts import run_ucope_shared_data_return_model_b03 as b03
from scripts import run_ucope_shared_data_return_model_b04 as b04


def test_synthetic_budget_defaults_and_publication(tmp_path, monkeypatch):
    original_collect = m.collect
    captured = []
    rows = {"train": 0, "eval": 0}
    expected_seed = None

    def collect(model, training, check_time, batches, seed):
        assert model.exposure()["scalar_value_updates"] == 0
        captured.append((batches, seed))
        # Exercise all 512 selected batches; historical default calls use one fixture batch.
        original_collect(model, training, check_time,
                         batches=batches if batches == 512 else 1, seed=seed)

    def synthetic_host(context, **kw):
        assert kw["ancestry"] == (m.OBJECT_ID, f"seed-{expected_seed}", m.context_id(context))
        probe = kw["root_action"] == "PROBE"
        if kw["evaluation"]:
            assert kw["episode_index"] == (rows["eval"] // 3) % 4096
            rows["eval"] += 1
        else:
            assert kw["episode_index"] == 32 * (rows["train"] // 256) + rows["train"] % 32
            rows["train"] += 1
        period = kw["tail_selector"](0) if probe else kw["immediate_period"]
        return m.host.Execution(0 if probe else None, kw["root_action"], period,
                                .5, -.1 if probe else 0., .5, 8 if probe else 2)

    monkeypatch.setattr(b02, "collect", collect)
    monkeypatch.setattr(m.host, "execute_episode", synthetic_host)
    for entry, seed, batches in [(b04, 6601, 512), (b04, 6602, 512),
                                 (b02, 6401, 1024), (b03, 6501, 1024)]:
        expected_seed = seed
        rows.update(train=0, eval=0)
        out = tmp_path / str(seed)
        monkeypatch.setattr("sys.argv", [entry.__name__, "--seed", str(seed), "--out", str(out)])
        assert entry.main() == 0
        summary = json.loads((out / "summary.json").read_text())
        assert captured[-1] == (batches, seed)
        assert summary["selected_batches"] == batches
        assert f"{batches}*T_batch256_shared_fit" in summary["cost_law"]
        assert summary["selected_eval_episodes_per_context_policy"] == 4096
        assert summary["object_id"] == entry.OBJECT_ID and summary["seed"] == seed
        assert summary["status"] == "COMPLETE"
        actual_batches = batches if entry is b04 else 1
        assert rows == {"train": actual_batches * 256, "eval": 98304}
        assert summary["training"]["batches_completed"] == actual_batches
        assert summary["training"]["episodes"] == actual_batches * 256
        assert summary["exposure"]["scalar_value_updates"] == actual_batches * 384
        assert summary["exposure"]["histogram_updates"] == actual_batches * 128
        assert all(c["complete"] and c["paired_episodes"] == 4096
                   for c in summary["evaluation"]["contexts"])
        assert all(x["episodes"] == 32768 for x in summary["evaluation"]["counts"].values())
        assert b02.BATCHES == m.BATCHES == 1024 and b02.EVAL_EPISODES == 4096
