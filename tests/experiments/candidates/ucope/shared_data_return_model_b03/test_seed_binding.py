"""Explicit seed propagation and publication over synthetic host rows only."""

import json
import random

from experiments.candidates.ucope.shared_data_return_model_b02 import model as m
from scripts import run_ucope_shared_data_return_model_b02 as b02
from scripts import run_ucope_shared_data_return_model_b03 as b03


def test_synthetic_seed_binding_and_publication(tmp_path, monkeypatch):
    monkeypatch.setattr(b02, "BATCHES", 2)
    monkeypatch.setattr(b02, "EVAL_EPISODES", 2)
    global_state = random.getstate()
    captures, models = {}, []
    original_model = m.ReturnModel

    def fresh_model():
        model = original_model()
        assert model.exposure()["scalar_value_updates"] == 0
        models.append(model)
        return model

    monkeypatch.setattr(b02, "ReturnModel", fresh_model)
    for seed in (6501, 6502, 6401):
        generator = random.Random(2_000_000 + seed)
        expected_uniforms = [generator.random() for _ in range(512)]
        training, evaluation = [], []

        def synthetic_host(context, **kw):
            assert kw["ancestry"] == ("UCOPE-SHARED-DATA-RETURN-MODEL-B02", f"seed-{seed}", m.context_id(context))
            assert kw["support"] == (2, 4, 6, 8)
            probe = kw["root_action"] == "PROBE"
            if not kw["evaluation"]:
                row = len(training)
                assert m.CONTEXTS.index(context) == (row % 256) // 32
                assert kw["episode_index"] == 32 * (row // 256) + row % 32
                assert probe == (row % 32 >= 16)
                period = kw["tail_selector"](object()) if probe else kw["immediate_period"]
                assert period == (m.K_EVAL[int(4 * expected_uniforms[row])] if probe else 4)
                training.append((kw["ancestry"], kw["episode_index"], period))
                # Distinct seed-specific values reveal accidental retained state.
                reward = seed / 10000.0
            else:
                assert len(training) == 512
                assert kw["episode_index"] == (len(evaluation) // 3) % 2
                period = kw["tail_selector"](0) if probe else kw["immediate_period"]
                evaluation.append((kw["ancestry"], kw["episode_index"]))
                reward = .5
            return m.host.Execution(0 if probe else None, kw["root_action"], period, reward,
                                    -.1 if probe else 0., reward, 8 if probe else 2)

        monkeypatch.setattr(m.host, "execute_episode", synthetic_host)
        out = tmp_path / str(seed)
        if seed == 6401:
            assert b02.run(out) == 0  # unchanged original default and identity
        else:
            monkeypatch.setattr("sys.argv", ["run_ucope_shared_data_return_model_b03.py",
                                            "--seed", str(seed), "--out", str(out)])
            assert b03.main() == 0
        summary = json.loads((out / "summary.json").read_text())
        assert summary["seed"] == seed and summary["status"] == "COMPLETE"
        assert summary["object_id"] == (m.OBJECT_ID if seed == 6401 else b03.OBJECT_ID)
        assert summary["independent_datasets"] == 1
        assert summary["training"]["episodes"] == summary["training"]["behavior_uniforms"] == 512
        assert summary["exposure"]["scalar_value_updates"] == 768
        assert summary["learned_values_and_counts"]["q_immediate"] == [seed / 10000.0] * 8
        assert len(evaluation) == 48
        assert all(v["mean"] == 0 for v in summary["evaluation"]["differences"].values())
        for row in range(0, 48, 3):
            assert evaluation[row] == evaluation[row + 1] == evaluation[row + 2]
        captures[seed] = training, evaluation
        assert m.SEED == b02.SEED == 6401 and m.OBJECT_ID.endswith("B02")
        assert random.getstate() == global_state
    assert not ({a for a, _, _ in captures[6501][0]} & {a for a, _, _ in captures[6502][0]})
    assert not (set(captures[6501][1]) & set(captures[6502][1]))
    assert models[0] is not models[1] and models[0].q_full is not models[1].q_full
    assert models[0].q_immediate == [.6501] * 8  # later calls did not mutate earlier state
