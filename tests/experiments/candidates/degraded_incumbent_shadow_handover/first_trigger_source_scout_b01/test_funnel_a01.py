from io import BytesIO
import json
import time

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01 import funnel_a01 as funnel
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    B01PreparedBatch, _B01PreparedTick, _State, empty_step_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    ExactPolicyGraph, WelfordState,
)
from scripts import run_dish_prefix_trigger_funnel_a01 as runner


def test_first_absent_order_and_last_live_completion_latch():
    c = dict.fromkeys(funnel.EVENTS, 0)
    assert funnel.row_label(c, False) == ("NO_LIVE_RENEWAL", None)
    c["live_renewal"] = 1
    assert funnel.row_label(c, False) == ("NO_PREPARE_PROPOSAL", None)
    c["prepare_proposal"] = 1
    assert funnel.row_label(c, False) == ("PREPARATION_SUPPORT_GAP", "latch")
    c["completion_latch"] = 1
    assert funnel.row_label(c, False) == ("PREPARATION_SUPPORT_GAP", "snapshot_delivery")
    c["snapshot_delivery"] = 1
    assert funnel.row_label(c, False) == ("PREPARATION_SUPPORT_GAP", "version_ready")
    c["version_ready"] = 1
    assert funnel.row_label(c, False) == ("NO_COMMIT_PROPOSAL", None)
    c["commit_proposal"] = 1
    assert funnel.row_label(c, False) == ("NO_EMITTED_INTENT", None)
    c["intent_emitted"] = 1
    assert funnel.row_label(c, False) == ("PENDING_INTENT_NOT_APPLICATION_VALID", None)
    assert funnel.row_label(c, True) == ("APPLICATION_VALID", None)


def test_copied_boundary_times_margin_terminal_and_counter_delta():
    prepared = _B01PreparedTick()
    s = prepared.state
    s.tick = 10; s.owner = 1; s.invalid_commit = 3
    s.readiness_accepted = 1; s.readiness_tick = 9
    s.snapshot_tick = 10; s.readiness_snapshot_tick = 10
    s.source_exists[:] = [1, 1]; s.source_sequence[:] = [7, 7]
    s.pending_intent = 1; s.pending_intent_margin = 5.9; s.intent_certificate = 1
    s.intent_origin_tick = 9
    s.battery[:] = [100, 100]; s.p[:] = [0, 0, 20, 0]
    prepared.snapshot_delivered = 1; prepared.readiness_delivered = 1
    prepared.observation.renew = 1
    counter = funnel.PrefixCounts()
    live, renew, version = counter.prepared(prepared)
    assert (live, renew, version) == (True, True, True)
    actions = empty_step_rows(1)
    actions["prepare"][0, 1] = 1; actions["commit"][0, 1] = 1
    completed = _State.from_buffer_copy(bytes(s))
    completed.tick = 11; completed.prepare_latched = 1; completed.warmup = 1
    completed.intent_origin_tick = 10; completed.pending_intent_margin = 8
    completed.terminal = 1; completed.invalid_commit = 4
    out = {"cas_applied": [0], "service": [1], "application_reason": [2]}
    counter.completion(prepared, actions, completed, out, live, renew, version)
    c = counter.counts
    assert c["prepared_latch"] == 0 and c["completion_latch"] == 1
    assert c["version_ready_renewal_completion_latch_commit"] == 1
    assert c["pending_low_margin_certificate"] == 1 and c["intent_emitted"] == 1
    assert c["invalid_commit"] == 1 and c["cas_applied"] == 0
    first = counter.first["intent_emitted"]
    assert first["action_tick"] == 10 and first["tick"] == 11 and first["owner"] == 1
    assert counter.first["terminal"]["battery"] == [100, 100]
    assert counter.first["terminal"]["separation"] == 20
    padding = _B01PreparedTick(); padding.state = completed; padding.observation.renew = 1
    live, renew, version = counter.prepared(padding)
    assert not live and not renew
    terminal_after = _State.from_buffer_copy(bytes(completed)); terminal_after.tick = 12
    # Native terminal outputs can zero-fill counters; persistent state must supply the delta.
    counter.completion(padding, actions, terminal_after,
                       {"cas_applied": [0], "service": [0], "application_reason": [0]},
                       live, renew, version)
    assert c["invalid_commit"] == 1 and c["intent_emitted"] == 1
    assert c["live_renewal"] == c["prepare_proposal"] == c["commit_proposal"] == 1
    assert c["terminal_padding"] == 1 and c["pending_high_margin_certificate"] == 1
    assert counter.reasons == {2: 1, 0: 1}
    assert counter.first["terminal"]["action_tick"] == 10
    padding.state = terminal_after
    counter.prepared(padding)  # Stale pending intent persists in native terminal padding.
    assert c["pending_prepared"] == 2 and c["pending_high_margin_certificate"] == 1
    assert c["terminal"] == 1
    s.readiness_tick = 8
    assert funnel.PrefixCounts().prepared(prepared)[2] is False


def test_valid_boundary_is_inspected_without_completion(monkeypatch):
    values = (_B01PreparedTick * 1)()
    values[0].origin_valid = 1; values[0].state.tick = 0
    prepared = B01PreparedBatch(values, 1)
    monkeypatch.setattr(funnel, "prepare_b01_application", lambda **kw: (prepared, {}, None))
    row = funnel.trace_prefix(None, None, max_ticks=2, deadline=time.perf_counter() + 10)
    assert row["triggered"] and row["inspected_boundaries"] == 1
    assert row["completed_ticks"] == 0 and row["label"] == "APPLICATION_VALID"


def test_real_toy_publication_smoke_and_original_prefix_identity(tmp_path, monkeypatch, capsys):
    started = time.perf_counter()
    torch.set_num_threads(1)
    model = ExactPolicyGraph()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        model.prepare.bias.fill_(-8); model.commit.bias.fill_(-8)
    stream = BytesIO()
    torch.save({"model": model.state_dict(), "optimizer": {}, "update": 0,
                "welford": {"actor": WelfordState.empty(54), "snapshot": WelfordState.empty(18),
                            "critic": WelfordState.empty(58)}}, stream)
    checkpoint = tmp_path / "toy.pt"; checkpoint.write_bytes(stream.getvalue())
    admission = tmp_path / "admission.json"
    admission.write_text(json.dumps({"passed": True, "physical_floor_pass": True,
                                    "effective_floor_pass": True, "available_physical_bytes": 2**33,
                                    "effective_available_bytes": 2**33}), encoding="utf-8")
    coordinate = funnel.panel()[0]
    native_factory = funnel.native_batch_from_rows
    policy_type = funnel.BatchedRecurrentPolicy
    captured = {}
    def capture_native(rows):
        captured["native"] = native_factory(rows)
        return captured["native"]
    def capture_policy(**kwargs):
        captured["policy"] = policy_type(**kwargs)
        return captured["policy"]
    monkeypatch.setattr(funnel, "panel", lambda: (coordinate,))
    monkeypatch.setattr(funnel, "PREFIX_TICKS", 6)
    monkeypatch.setattr(funnel, "native_batch_from_rows", capture_native)
    monkeypatch.setattr(funnel, "BatchedRecurrentPolicy", capture_policy)
    output = tmp_path / "published"
    assert runner.main(["run", "--seed", "11", "--checkpoint", str(checkpoint),
                        "--admission", str(admission), "--out", str(output)]) == 0
    result = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(capsys.readouterr().out) == result
    assert result["rows"][0]["completed_ticks"] == 6
    assert result["result"] == "A01-REPLAY-DISCREPANCY"  # Toy size differs from formal reference.
    assert result["new_exposure"]["maximum_l2_displacement"] == 0
    assert result["new_exposure"]["optimizer_steps"] == 0
    assert result["measured_cost"]["wall_seconds"] > 0
    assert result["peak_rss_bytes"] > 0 or result["resources_unmeasured"]
    assert checkpoint.read_bytes() == stream.getvalue()
    native = native_factory((funnel._reset_row(funnel.seed_master(11), coordinate),))
    policy = policy_type(arm="STRUCTURED", checkpoint_bytes=stream.getvalue(),
                         state=funnel.RecurrentRolloutState.fresh("STRUCTURED", width=1))
    for tick in range(6):
        prepared, observation, _ = funnel.prepare_b01_application(native=native, policy=policy)
        assert not prepared.origin_valid[0]
        rows = policy.step_rows(observation, sampler=funnel._DeterministicSampler(), global_tick=tick,
                                deterministic=True, recurrent_prepared=True)
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        after = native.complete_b01_tick(prepared, rows)
        policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=after)
    assert native.snapshot_bytes() == captured["native"].snapshot_bytes()
    assert torch.equal(policy.state.hidden, captured["policy"].state.hidden)
    assert policy.state.actor_welford.count == captured["policy"].state.actor_welford.count
    assert runner.project_cost()["projected_seconds"] == 450
    assert time.perf_counter() - started < 60
