import ctypes
from io import BytesIO
import hashlib
import json
import math
import subprocess
import time

import numpy as np
import torch
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01 import native_a03, path_a03 as path
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import ExactPolicyGraph, WelfordState
from scripts import run_dish_ground_endpoint_path_a03 as runner
from scripts.run_dish_ground_source_point_a02 import terrain


def test_reading_and_old_packet_on_cas_is_not_promoted_owner_consequence():
    counts = path.PathCounts()
    assert path.read_rule(counts.counts)["result"] == "A03-ACCESS-NOT-RESTORED"
    for key in ("camera_u0", "camera_u1", "source_u0_adoption", "source_u1_adoption", "common_source"):
        counts.counts[key] = 1
    assert path.read_rule(counts.counts)["earliest_absent_stage"] == "snapshot_delivery"
    for key in ("snapshot_delivery", "readiness_delivery", "origin_valid"):
        counts.counts[key] = 1
    before = backend._State(); before.tick = 10
    before.pending_relay_exists = 1; before.pending_relay_tick = 9; before.pending_relay_sender = 0
    prepared = backend._B01PreparedTick(); prepared.state = before; prepared.observation.renew = 1
    prepared.state.base_exists = 1; prepared.state.base_relay_tick = 9
    counts.arrivals(before, prepared)
    after = backend._State.from_buffer_copy(bytes(prepared.state))
    after.owner = 1; after.actuator_owner = 1; after.service_epoch = 1; after.tick = 11
    output = {"cas_applied": [1], "service": [1], "application_reason": [0]}
    rows = backend.empty_step_rows(1)
    consequence = counts.completion(prepared, rows, after, output)
    assert consequence["legal_transfer"] and not consequence["qualified_service"]
    assert counts.counts["service_at_or_after_transfer"] == 1
    assert counts.counts["service_after_transfer_old_or_other_packet"] == 1
    assert path.read_rule(counts.counts)["result"] == "A03-CONSEQUENCE-NOT-REACHED"
    # Same SOURCE packet, newly relayed by the new owner, must count as a new base adoption.
    before = backend._State.from_buffer_copy(bytes(after))
    before.pending_relay_sender = 1; before.pending_relay_tick = 10
    prepared.state = before; prepared.state.base_relay_tick = 10
    arrival = counts.arrivals(before, prepared)
    assert arrival["base_adopted"] and arrival["adopted_base_sender"] == 1
    after = backend._State.from_buffer_copy(bytes(prepared.state)); after.tick = 12
    output["cas_applied"] = [0]
    assert counts.completion(prepared, rows, after, output)["qualified_service"]
    assert path.read_rule(counts.counts)["result"] == "A03-BOUNDED-PATH-QUALIFIED"
    assert counts.counts["base_adoption"] == 2


def test_source_adoption_requires_actual_receiver_change_not_margin():
    before = backend._State(); before.tick = 4
    before.pending_source_exists = 1; before.pending_source_sequence = 3
    before.pending_source_margin[:] = [12, 12]
    prepared = backend._B01PreparedTick(); prepared.state = before
    prepared.state.source_exists[1] = 1; prepared.state.source_sequence[1] = 3
    prepared.state.source_tick[1] = 3
    counts = path.PathCounts()
    assert counts.arrivals(before, prepared)["source_adopted"] == [False, True]
    unchanged = backend._State.from_buffer_copy(bytes(prepared.state))
    assert counts.arrivals(unchanged, prepared)["source_adopted"] == [False, False]


@pytest.mark.parametrize("terminal_prepared", [False, True])
def test_valid_boundary_continues_but_terminal_prepared_does_not_act(monkeypatch, terminal_prepared):
    calls = []
    class Native:
        def __init__(self, *args):
            self.state = backend._State()
        def state_copy(self):
            return backend._State.from_buffer_copy(bytes(self.state))
        def prepare_b01_tick(self):
            values = (backend._B01PreparedTick * 1)()
            values[0].state = self.state
            values[0].state.terminal = int(terminal_prepared)
            values[0].origin_valid = int(not terminal_prepared)
            return backend.B01PreparedBatch(values, 1)
        def complete_b01_tick(self, prepared, rows):
            calls.append("complete")
            self.state.tick = 1; self.state.terminal = 1
            return {"cas_applied": [0], "service": [0], "application_reason": [0]}
    class Policy:
        def __init__(self, **kwargs):
            self.model = torch.nn.Linear(1, 1)
        def prepare_recurrent(self, observation):
            calls.append("prepare")
        def normalized_actor(self, observation):
            return torch.as_tensor(observation["actor"], dtype=torch.float32)
        def step_rows(self, *args, **kwargs):
            calls.append("forward")
            return backend.empty_step_rows(1)
        def apply_native_promotion(self, **kwargs):
            calls.append("promotion")
    monkeypatch.setattr(path, "PointBatch", Native)
    monkeypatch.setattr(path, "load_host", lambda host: None)
    monkeypatch.setattr(path, "BatchedRecurrentPolicy", Policy)
    from io import StringIO
    stream = StringIO()
    result = path.run_host(native_a03.HOSTS[0], {}, b"", stream, time.perf_counter() + 30)
    assert calls == ([] if terminal_prepared else ["prepare", "forward", "complete", "promotion"])
    assert result["inspected_boundaries"] == 1
    assert result["completed_ticks"] == int(not terminal_prepared)
    assert result["stop"] == "native_terminal"
    assert result["counts"]["origin_valid"] == int(not terminal_prepared)


def toy_checkpoint():
    model = ExactPolicyGraph()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        model.prepare.bias.fill_(-8); model.commit.bias.fill_(-8)
    stream = BytesIO()
    torch.save({"model": model.state_dict(), "optimizer": {}, "update": 0,
                "welford": {"actor": WelfordState.empty(54), "snapshot": WelfordState.empty(18),
                            "critic": WelfordState.empty(58)}}, stream)
    return stream.getvalue()


def advance(native, checkpoint, ticks):
    policy = path.BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=checkpoint,
                                        state=path.RecurrentRolloutState.fresh("STRUCTURED", width=1))
    for tick in range(ticks):
        prepared = native.prepare_b01_tick(); observation = prepared.observe()
        policy.prepare_recurrent(observation)
        rows = policy.step_rows(observation, sampler=path.study._DeterministicSampler(), global_tick=tick,
                                deterministic=True, recurrent_prepared=True)
        owner = np.asarray(observation["owner"], dtype=np.int64)
        after = native.complete_b01_tick(prepared, rows)
        policy.apply_native_promotion(owner_before=owner, step_rows=rows, observation_after=after)
    return policy


def python_ray(s, a, b, clearance, from_ground, tapered):
    for j in range(1, 128):
        u = j / 128
        q = u if from_ground else 1 - u
        x, y, z = (a[i] + u * (b[i] - a[i]) for i in range(3))
        if z <= terrain(x, s.reflection * y) + clearance * (q if tapered else 1):
            return True
    return False


def test_real_different_fixture_publication_geometry_and_literal_identity(tmp_path, monkeypatch, capsys):
    started = time.perf_counter()
    original_panel = path.study.panel()
    coordinate = original_panel[1]  # Never the carded panel()[0] A03 fixture.
    assert coordinate != original_panel[0]
    monkeypatch.setattr(path.study, "panel", lambda: (coordinate,))
    monkeypatch.setattr(path, "MAX_TICKS", 3)
    saved = []
    batch_type = path.PointBatch
    def capture(library, reset):
        batch = batch_type(library, reset)
        saved.append(batch)
        return batch
    monkeypatch.setattr(path, "PointBatch", capture)
    checkpoint = tmp_path / "toy.pt"; checkpoint.write_bytes(toy_checkpoint())
    output = tmp_path / "published"
    assert runner.main(["run", "--seed", "11", "--checkpoint", str(checkpoint),
                        "--admission", str(tmp_path / "external-receipt.json"), "--out", str(output)]) == 0
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary == json.loads(capsys.readouterr().out)
    assert len(summary["hosts"]) == 2
    assert all(h["completed_ticks"] == 3 and h["parameter_change"]["l2_displacement"] == 0
               for h in summary["hosts"])
    traces = [json.loads(line) for line in (output / "trace.jsonl").read_text().splitlines()]
    assert len(traces) == 6
    assert all(len(t["actor_raw"][0]) == 4 and t["actor_normalized"] is not None for t in traces)
    assert saved[0].library._handle != saved[1].library._handle
    # Default branch is equivalent to the exact pre-seam source, on this ordinary fixture only.
    source = subprocess.check_output(["git", "show", "6ce12ad227600ef3d58ec4a2466a741f1e94e7b2:"
                                     "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp"])
    key, _ = backend._build_material()
    key = hashlib.sha256(key.encode() + source).hexdigest()
    old_lib = backend._configure(ctypes.CDLL(str(backend._compile(key, source))))
    reset = path.study._reset_row(path.study.seed_master(11), coordinate)
    old = batch_type(old_lib, reset)
    advance(old, checkpoint.read_bytes(), 3)
    assert bytes(old.states) == bytes(saved[0].states)
    assert bytes(old.outputs) == bytes(saved[0].outputs)
    # Verify both ground distances and tapered rays against independent scalar equations.
    candidate = batch_type(saved[1].library, reset)
    literal = batch_type(saved[0].library, reset)
    cp = backend._B01PreparedTick.from_buffer_copy(candidate.prepare_b01_tick().snapshot_bytes())
    lp = backend._B01PreparedTick.from_buffer_copy(literal.prepare_b01_tick().snapshot_bytes())
    s = cp.state
    ground = (cp.physics.gx, cp.physics.gy, terrain(cp.physics.gx, s.reflection * cp.physics.gy) + 2)
    literal_ground = (ground[0], ground[1], 0)
    for i in range(2):
        uav = (s.p[2*i], s.p[2*i+1], 90)
        d = math.sqrt(sum((a-b)**2 for a,b in zip(ground, uav)))
        old_d = math.sqrt(sum((a-b)**2 for a,b in zip(literal_ground, uav)))
        blocked = python_ray(s, ground, uav, 8, True, True)
        old_blocked = python_ray(s, literal_ground, uav, 8, True, False)
        expected_difference = -20*math.log10(max(d,1)/100) + 20*math.log10(max(old_d,1)/100) - 35*(blocked-old_blocked)
        assert abs((cp.physics.radio[i]-lp.physics.radio[i])-expected_difference) <= 1e-12
        expected_camera = not python_ray(s, uav, ground, 5, False, True) and d <= 500
        assert bool(cp.physics.camera_present[i]) == expected_camera  # Degradation inactive at toy tick 0.
    assert list(cp.physics.radio)[2:] == list(lp.physics.radio)[2:]
    assert runner.project_cost()["per_host_seconds"] == 88.47988453649668
    assert runner.project_cost()["pair_seconds"] == 176.95976907299337
    assert time.perf_counter() - started < 60
