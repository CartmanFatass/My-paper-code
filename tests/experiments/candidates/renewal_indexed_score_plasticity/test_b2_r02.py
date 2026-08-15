from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import b2_r02_experiment as experiment  # noqa: E402
import b2_r02_resume as resume  # noqa: E402


def test_structural_anchor_certificate_and_common_function_domain() -> None:
    certificate = experiment.structural_certificate()
    assert certificate["passed"] is True
    assert certificate["recurrent_scalars_each"] == 39
    assert certificate["rows"]["1"]["delta_v"] == pytest.approx(40 / 171, abs=2**-40)
    assert certificate["rows"]["1"]["tv"] == pytest.approx(40 / 171, abs=2**-40)
    assert certificate["rows"]["-1"]["delta_v"] == pytest.approx(35 / 726, abs=2**-40)
    assert certificate["rows"]["-1"]["tv"] == pytest.approx(35 / 363, abs=2**-40)

    anchor = experiment.DirectModel(0, "DIRECT-ANCHOR")
    contain = experiment.DirectModel(0, "DIRECT-CONTAIN")
    for name in ("w1", "b1", "w2", "b2", "base", "base_b"):
        assert torch.equal(getattr(anchor, name), getattr(contain, name))
    assert torch.equal(anchor.E, experiment.g_matrix())
    assert torch.equal(contain.E, torch.zeros_like(contain.E))
    assert anchor.E.shape == contain.E.shape == (3, 13)
    assert anchor.E.numel() == contain.E.numel() == 39


def test_schedule_lifecycle_and_physical_windows() -> None:
    assert [(len(experiment.schedule_rows(schedule)), sum(not row[2] for row in experiment.schedule_rows(schedule))) for schedule in range(5)] == [
        (48, 47),
        (24, 23),
        (16, 15),
        (32, 31),
        (32, 31),
    ]
    switch_up = experiment.schedule_rows(3)
    switch_down = experiment.schedule_rows(4)
    assert switch_up[24][:2] == (96, 12)
    assert switch_down[8][:2] == (96, 4)
    assert experiment.Q_WINDOWS[3] == (108, 192)
    assert experiment.Q_WINDOWS[4] == (100, 192)


def test_exact_tape_is_reused_without_architecture_or_feedback_address() -> None:
    probabilities = (experiment.interval_ratio(1, 3),) * 3
    identity = experiment.event_identity(7, "EVAL", 4, 11, 1, 3, "ACTION")
    first_audit = experiment.SamplerAudit()
    second_audit = experiment.SamplerAudit()
    assert experiment.exact_cat(probabilities, identity, "ACTION", first_audit) == experiment.exact_cat(probabilities, identity, "ACTION", second_audit)
    assert first_audit.calls == second_audit.calls == {"ACTION": 1}
    assert "RISP-B1" not in experiment._identity_bytes(identity).decode("ascii")


def test_one_update_micro_path_has_exact_lifecycle_ledger() -> None:
    audit = experiment.SamplerAudit()
    model = experiment.DirectModel(123, "DIRECT-ANCHOR", audit)
    packet = experiment.train_model(model, 123, audit, updates=1, episodes_per_batch=2)
    assert packet["updates"] == 1
    assert audit.calls == {
        "INIT_MODEL": 60,
        "INIT_TARGET": 4,
        "ACTION": 144,
        "OUTCOME": 144,
        "ALT": 144,
    }
    assert all(torch.isfinite(parameter).all() for parameter in model.parameters())


def test_intact_and_twin_evaluation_preserve_counts_and_twin_separation() -> None:
    model = experiment.DirectModel(321, "DIRECT-CONTAIN")
    intact_audit = experiment.SamplerAudit()
    twin_audit = experiment.SamplerAudit()
    intact = experiment.evaluate_architecture_cell(model, 321, 2, "INTACT", intact_audit, episodes=1)
    twin = experiment.evaluate_architecture_cell(model, 321, 2, "MARGINAL-TWIN", twin_audit, episodes=1)
    assert intact["decisions"] == twin["decisions"] == 32
    assert intact["updates"] == twin["updates"] == 30
    assert intact["diagnostic"]["rows"] == twin["diagnostic"]["rows"] == 30
    assert "TWIN" not in intact_audit.calls
    assert twin_audit.calls["TWIN"] == 30
    for kind in ("INIT_TARGET", "ACTION", "OUTCOME", "ALT"):
        assert intact_audit.calls[kind] == twin_audit.calls[kind]


def test_production_rss_is_observable() -> None:
    peak = resume._peak_rss_bytes()
    assert isinstance(peak, int) and peak > 0
