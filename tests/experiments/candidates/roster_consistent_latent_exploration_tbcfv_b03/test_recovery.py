"""No-native recovery check: completed supplied-graph block survives next-block failure."""
import json
import time
from types import SimpleNamespace
import torch
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import make_conformance_fixture_model


def test_completed_block_survives_exception(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    model = make_conformance_fixture_model()
    authority = SimpleNamespace(root_digest="fixture", certificate={"native": "not invoked"})
    monkeypatch.setattr(study, "make_rng", lambda seed=study.SEED: (authority, SimpleNamespace(block_index=0)))
    monkeypatch.setattr(study, "initialize_block_models", lambda rng: {study.FLEX: model})
    calls = []
    def supplied(model, arm, rng, coords, training):
        calls.append((arm, coords[0].update_or_scenario))
        if coords[0].update_or_scenario == 1:
            raise RuntimeError("injected next-block failure")
        return [SimpleNamespace(Y=.5, U=.4, tau=40., F=0., agent_ticks=1, claim_decisions=1,
                                plan_scores=[model.manager_mean.bias.sum()],
                                claim_scores=[model.pointer_score.bias.sum()]) for _ in coords]
    monkeypatch.setattr(study, "execute_learned_batch", supplied)
    before = study.host.flat_parameters(model).clone()
    result = study.run("W100", tmp_path, "fixture", tmp_path / "no-admission",
                       time.perf_counter(), 600)
    rows = [json.loads(line) for line in (tmp_path / "completed_blocks.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows == result["curves"]
    assert rows[0]["update"] == 0 and rows[0]["training_episodes"] == 64
    assert rows[0]["event_order"] == ["parameter_update", "baseline_update"]
    torch.testing.assert_close(torch.tensor(rows[0]["raw_gradient_norm"]), torch.tensor((4*.5**2+50**2)**.5))
    torch.testing.assert_close(torch.linalg.vector_norm(study.host.flat_parameters(model)-before), torch.tensor(.02,dtype=torch.float64))
    assert result["counts"]["backward_step_calls"] == 1
    assert result["status"] == "TECHNICAL_STOP"
    assert result["stop_reason"] == "RuntimeError: injected next-block failure"
    assert calls == [(study.FLEX,0),(study.FLEX,0),(study.FLEX,1)]
    assert json.loads((tmp_path / "summary.json").read_text())["curves"] == rows
