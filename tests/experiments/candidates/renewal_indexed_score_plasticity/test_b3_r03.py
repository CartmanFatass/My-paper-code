from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import b3_r03_experiment as experiment  # noqa: E402
import b3_r03_resume as resume  # noqa: E402


def test_structural_certificate_and_function_equivalence() -> None:
    certificate = experiment.structural_certificate()
    assert certificate["passed"] is True
    assert certificate["slow_scalars_each"] == 75
    assert certificate["recurrent_scalars_each"] == 39
    assert certificate["trainable_scalars_each"] == 114
    anchor = experiment.TrackModel(0, "TRACK-G-ANCHOR")
    contain = experiment.TrackModel(0, "TRACK-CONTAIN")
    for name in ("w1", "b1", "w2", "b2", "w3", "b3"):
        assert torch.equal(getattr(anchor, name), getattr(contain, name))
    assert torch.equal(anchor.E, experiment.g_matrix())
    assert torch.equal(contain.E, torch.zeros_like(contain.E))
    assert anchor.E.shape == contain.E.shape == (3, 13)


def test_schedule_windows_and_registered_row_populations() -> None:
    assert [(len(experiment.schedule_rows(index)), sum(not row[2] for row in experiment.schedule_rows(index))) for index in range(5)] == [(48, 47), (24, 23), (16, 15), (32, 31), (32, 31)]
    assert experiment.schedule_rows(3)[24][:2] == (96, 12)
    assert experiment.schedule_rows(4)[8][:2] == (96, 4)
    eligible = []
    for schedule in range(5):
        rows = experiment.schedule_rows(schedule)
        eligible.append(sum(experiment._target_row_eligible(schedule, rows[index + 1][0]) for index in range(len(rows) - 1)))
    assert eligible == [47, 23, 15, 7, 23]


def test_fresh_coordinate_namespace_and_paired_addresses() -> None:
    identity = experiment.event_identity(7, "TEST", 4, 11, 1, 3, "ACTION")
    assert experiment.COORDINATE_ROOT not in {"", "0" * 64}
    assert "RISP-B1" not in experiment._identity_bytes(identity).decode("ascii")
    assert "RISP-B2" not in experiment._identity_bytes(identity).decode("ascii")
    first = experiment.SamplerAudit()
    second = experiment.SamplerAudit()
    probabilities = tuple(experiment.interval_ratio(1, 3) for _ in range(3))
    assert experiment.exact_cat(probabilities, identity, "ACTION", first) == experiment.exact_cat(probabilities, identity, "ACTION", second)
    assert first.calls == second.calls == {"ACTION": 1}


def test_software_tanh_matches_high_precision_reference() -> None:
    values = torch.tensor([[-20.0, -1.0, -0.0, 0.125, 1.0, 20.0]], dtype=torch.float64, requires_grad=True)
    observed = experiment._cr_tanh(values)
    expected = torch.tensor(experiment._tanh_values(values.detach().reshape(-1).tolist(), 180), dtype=torch.float64).reshape_as(values)
    assert torch.equal(observed, expected)
    observed.sum().backward()
    assert torch.isfinite(values.grad).all()


def test_one_update_two_episode_training_micro_path() -> None:
    packet = experiment.run_training_unit(31, "TRACK-G-ANCHOR", updates=1, episodes=2)
    assert packet["registered"] is False
    assert packet["updates"] == 1
    assert packet["sampler_audit"]["calls"] == {"ACK": 144, "ACTION": 144, "INIT_MODEL": 60, "INIT_SECTOR": 4, "MOTION": 144}
    assert all(checkpoint["finite"] for checkpoint in packet["training"]["checkpoints"].values())


def test_single_episode_uniform_evaluation_lifecycle() -> None:
    packet = experiment.run_evaluation_unit(29, "UNIFORM", 2, {}, episodes=1)
    result = packet["result"]
    assert packet["registered"] is False
    assert result["decisions"] == 32
    assert result["updates"] == 0
    assert result["min_support"] == pytest.approx(1 / 3)
    assert packet["sampler_audit"]["calls"] == {"ACK": 32, "ACTION": 32, "INIT_SECTOR": 2, "MOTION": 32}


def _fake_eval(seed: int, cell: str, schedule: int) -> dict:
    q = 0.4
    if cell == "STATE-ORACLE":
        q = 0.8
    elif cell == "CONTAIN-G-BOUND":
        q = 0.62
    elif cell.endswith("|INTACT"):
        q = 0.65 if cell.startswith("TRACK-G") else 0.60
    elif cell.endswith("|MARGINAL-TWIN"):
        q = 0.595 if cell.startswith("TRACK-G") else 0.59
    elif cell.endswith("|NO-RECURRENCE"):
        q = 0.50
    elif cell.endswith("|FIXED-PERSIST"):
        q = 0.49
    elif cell.endswith("|GLOBAL-RATE"):
        q = 0.48
    diagnostic = None
    if cell == "CONTAIN-G-BOUND" or cell.endswith("|INTACT") or cell.endswith("|MARGINAL-TWIN"):
        diagnostic = {"rows": {0: 47, 1: 23, 2: 15, 3: 7, 4: 23}[schedule] * 128, "tv_ge_001_fraction": 0.8, "delta_positive_fraction": 0.8, "delta_mean": 0.02, "tv_mean": 0.1}
    support = 1 / 3 if cell == "UNIFORM" else (1 / 60 if cell == "STATE-ORACLE" else 0.1)
    decisions = len(experiment.schedule_rows(schedule)) * 128
    updates = (len(experiment.schedule_rows(schedule)) - 1) * 128 if cell not in ("UNIFORM", "STATE-ORACLE") else 0
    return {"schema": experiment.EVALUATION_SCHEMA, "science_revision": experiment.SCIENCE_REVISION, "algorithm_seed": seed, "cell": cell, "schedule_id": schedule, "registered": True, "result": {"q": q, "q_full": q, "decisions": decisions, "updates": updates, "min_support": support, "action_counts": [decisions, 0, 0], "ack_success_rate": 0.5, "direct_tv_max_residual": 0.0, "diagnostic": diagnostic}, "sampler_audit": {"calls": {}, "max_prefix_bits": {}}, "elapsed_seconds": 0.0}


def test_complete_analyzer_branch_precedence_on_deterministic_fixture() -> None:
    training = [{"schema": experiment.TRAINING_SCHEMA, "science_revision": experiment.SCIENCE_REVISION, "algorithm_seed": seed, "architecture": architecture, "registered": True, "updates": 512, "episodes_per_batch": 16} for seed in experiment.ALGORITHM_SEEDS for architecture in experiment.ARCHITECTURES]
    evaluation = [_fake_eval(seed, cell, schedule) for seed in experiment.ALGORITHM_SEEDS for cell in experiment.CELL_FAMILIES for schedule in range(5)]
    result = experiment.analyze_complete(training, evaluation)
    assert result["complete_panel"] is True
    assert result["validity"]["complete_16x5x13_panel"] is True
    assert result["branch"] == "TARGET_EXTERNAL_K_REALIZED_ACK_G_PRIOR_SUPPORTED"


def test_atomic_plan_and_resource_observability() -> None:
    assert len(resume.unit_plan()) == 1072
    assert len(set(resume.unit_plan())) == 1072
    assert resume._peak_rss_bytes() is None or resume._peak_rss_bytes() > 0
