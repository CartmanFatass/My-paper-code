"""One complete changed-path check; engineering exposure is not a B seed."""
import json
from fractions import Fraction
import subprocess

import torch

from experiments.candidates.capability_bound_semantic_currentness import direct_return_b02 as direct
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import Action
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.tapes import EpisodeTape
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.checkpoint import load_checkpoint


def test_two_arm_real_update_native_return_and_paired_readback(tmp_path, monkeypatch):
    project = direct.engine._project_panel
    evaluator = EpisodeTape.evaluator
    inside_projection = False
    projected_ids = []
    eval_tapes = {}

    def evaluator_without_policy_leak(self):
        assert not inside_projection, "public policy projection accessed evaluator truth"
        return evaluator(self)

    def checked_projection(tapes, factory):
        nonlocal inside_projection
        inside_projection = True
        try:
            observations, work = project(tapes, factory)
        finally:
            inside_projection = False
        assert observations.shape == (len(tapes), 152, 168)
        assert observations.dtype is torch.float32
        for tape, rows in zip(tapes, observations, strict=True):
            public = torch.tensor([token.float32_channels() for token in tape.learner_tokens()])
            assert torch.equal(rows[:, :136], public)
            if tape.identity.split == "EVAL_STOCHASTIC":
                eval_tapes[tape.identity.episode_id] = tape
        projected_ids.append([tape.identity.episode_id for tape in tapes])
        return observations, work

    monkeypatch.setattr(EpisodeTape, "evaluator", evaluator_without_policy_leak)
    monkeypatch.setattr(direct.engine, "_project_panel", checked_projection)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    raw = direct.run_arm(arm=direct.ARMS[0], seed=21201, output=tmp_path / "raw",
                         launch_sha=sha, engineering=True)
    structured = direct.run_arm(arm=direct.ARMS[1], seed=21201, output=tmp_path / "struct",
                                launch_sha=sha, engineering=True,
                                raw_result=tmp_path / "raw/summary.json")
    assert projected_ids == [[0], list(range(8)), [0], list(range(8))]
    assert raw["initialization_digest"] == structured["initialization_digest"]
    for name, result in (("raw", raw), ("struct", structured)):
        assert result["parameter_count"] == 121349
        assert result["parameter_movement_l2"] > 0 and result["changed_parameters"] > 0
        assert result["counters"] == {"rollout_updates": 1, "adam_steps": 16,
            "train_episodes": 8, "train_transitions": 1216, "train_decisions": 192}
        assert result["evaluation_executions"] == 2 and result["evaluation_transitions"] == 304
        updates = [json.loads(line) for line in (tmp_path / name / "updates.jsonl").read_text().splitlines()]
        assert len(updates) == 1 and len(updates[0]["losses"]) == 16
        assert updates[0]["episode_ids"] == list(range(8))
        assert all(torch.isfinite(torch.tensor(loss["total_loss"])) for loss in updates[0]["losses"])
        for update in (0, 1):
            checkpoint = load_checkpoint(tmp_path / name / f"update-{update}.pt")
            assert checkpoint["counters"]["adam_steps"] == 16 * update
        for evaluation in result["evaluations"]:
            assert evaluation["state"]["model_digest_before"] == evaluation["state"]["model_digest_after"]
            assert evaluation["optimizer_before"] == evaluation["optimizer_after"]
            assert evaluation["state"]["consumed_uniform_rows"] == []
            for row in evaluation["episodes"]:
                tape = eval_tapes[row["identity"]["episode_id"]]
                assert len(row["actions"]) == 24 and "WAIT" not in row["actions"]
                ledgers = [tape.evaluator().ledger(i, Action[action]) for i, action in enumerate(row["actions"])]
                native = sum((ledger.decision_reward + ledger.settlement_reward for ledger in ledgers), Fraction())
                assert native == direct.fraction(row["native_return"])
    refresh = raw["context"]["ALWAYS_REFRESH"][0]
    tape = eval_tapes[0]
    settlement = sum((tape.evaluator().ledger(i, Action.REFRESH).settlement_reward for i in range(24)), Fraction())
    assert settlement > 0
    assert direct.fraction(refresh["settlement_sum"]) == settlement
    assert direct.fraction(refresh["native_return"]) == direct.fraction(refresh["decision_sum"]) + settlement
    pair = json.loads((tmp_path / "struct/paired_summary.json").read_text())
    expected = direct.fraction(structured["evaluations"][-1]["episodes"][0]["native_return"]) - direct.fraction(raw["evaluations"][-1]["episodes"][0]["native_return"])
    assert len(pair["differences"]) == 1 and direct.fraction(pair["mean_difference"]) == expected
    assert pair["profile"] == "ENGINEERING_ONLY"
    print(json.dumps({"engineering_adam_steps": 32, "engineering_train_eval_transitions": 3040,
                      "arm_costs": [raw["cost"], structured["cost"]]}))
