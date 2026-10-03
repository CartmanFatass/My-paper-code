"""Pure fabricated evidence and fake backends; no scientific kernel executes."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b06_request_amortization import reader as r


class Meter:
    def __init__(self):
        self.counts, self.events = {}, []

    def check(self):
        self.events.append(("check",))

    def reserve(self, name, amount=1):
        self.events.append(("reserve", name, amount))
        self.counts[name] = self.counts.get(name, 0) + amount

    def add(self, name, amount=1):
        self.events.append(("add", name, amount))
        self.counts[name] = self.counts.get(name, 0) + amount

    def check_disk(self, **kwargs):
        self.events.append(("disk", kwargs))

    def report(self):
        return {"cumulative_cpu_seconds": 100., "phase_cpu_seconds": 80.}


def forbidden(*args, **kwargs):
    raise AssertionError("real scientific call forbidden in engineering checks")


@pytest.fixture(autouse=True)
def no_science(monkeypatch):
    for name in ("physical_state", "motion", "predict_g", "geometry", "future_arrivals", "commanded_motion"):
        monkeypatch.setattr(r, name, forbidden)
    monkeypatch.setattr(r.acq, "TorchBackend", forbidden)
    monkeypatch.setattr(r.acq.np.linalg, "solve", forbidden)


def fake_scorer(audit, output=None, fail=False):
    def forward(rows, *, training):
        assert not training
        assert audit.counts["neural_attempted_rows"] >= len(rows)
        if fail:
            raise RuntimeError("fabricated forward interruption")
        return np.zeros((len(rows) // 4, 4), np.float32) if output is None else output.copy()
    return SimpleNamespace(forward=forward)


def test_new_limits_and_reserve_before_fake_call():
    meter, audit = Meter(), r.Audit(Meter(), "source")
    audit.meter = meter
    assert audit.LIMITS == {"native_physical_attempts": 269024, "R_initial_physical_attempts": 3840,
                            "R_prefix_physical_attempts": 5201920, "G_attempts": 271488,
                            "G_reserved_candidate_ticks": 246912000, "neural_attempted_rows": 73440,
                            "scorer_constructor_attempts": 6}
    result = audit.infer(fake_scorer(audit), np.zeros((4, 303), np.float32))
    assert result.shape == (4,) and audit.counts["neural_rows"] == 4
    assert meter.events[:2] == [("check",), ("reserve", "reader_neural_attempted_rows", 4)]
    audit.counts["neural_attempted_rows"] = 73440
    with pytest.raises(AssertionError, match="exposure bound"):
        audit.infer(forbidden, np.zeros((4, 303), np.float32))


def test_failed_fake_forward_retains_attempt_and_no_completion():
    audit = r.Audit(Meter(), "source")
    with pytest.raises(RuntimeError, match="interruption"):
        audit.infer(fake_scorer(audit, fail=True), np.zeros((4, 303), np.float32))
    assert audit.counts == {"neural_attempted_rows": 4, "deployment_neural_attempts": 1}


def test_bank_adapter_counts_rows_once_and_combines_deployment():
    audit = r.Audit(Meter(), "source")
    adapter = r.NeuralMeter(audit)
    for fit in range(3):
        for stage in ("initial", "final"):
            phase = f"b06_reader_fit{fit}_{stage}_bank"
            adapter.reserve(phase + "_forward_attempted_rows", 8400)
            adapter.add(phase + "_forward_rows", 8400)
            adapter.reserve(f"b06_reader_load_fit{fit}_{stage}_scorer_constructor_attempts")
            adapter.add(f"b06_reader_load_fit{fit}_{stage}_scorer_constructors")
    audit.infer(fake_scorer(audit), np.zeros((4, 303), np.float32))
    assert audit.counts["neural_attempted_rows"] == audit.counts["neural_rows"] == 50404
    assert audit.counts["bank_neural_rows"] == 50400 and audit.counts["deployment_neural_rows"] == 4
    assert audit.counts["scorer_constructor_attempts"] == audit.counts["scorer_constructors"] == 6
    assert audit.meter.counts["reader_neural_attempted_rows"] == 50404


def arrays_for_score(raw, residual, total, chosen, *, scored=True, neural=True):
    return dict(nn_complete=np.array([neural]), score_complete=np.array([scored]),
                residual=np.array([residual], np.float32), total_q=np.array([total], np.float64),
                greedy_action=np.array([chosen], np.int8))


@pytest.mark.parametrize("eligible,expected", [(False, 0), (True, 1)])
def test_student_late_cache_lex_order_and_command_permission(eligible, expected):
    raw = np.array([1200., 0., 2400., 3600.])
    residual = np.array([-1., 0., 0., 0.], np.float32)
    total = raw / 1200. + residual.astype(np.float64)
    audit = r.Audit(Meter(), "source")
    arrays = arrays_for_score(raw, residual, total, 1)
    scorer = fake_scorer(audit, residual.reshape(1, 4))
    assert r.score_and_command(arrays, 0, "S0", raw, np.zeros((4, 303), np.float32),
                               eligible, audit, {(0, "final"): scorer}, None) == expected
    assert audit.counts["deployment_neural_rows"] == 4


def test_B_uses_raw_G_units_and_late_cache_keeps_command():
    raw, correction = np.array([10., 8., 30., 40.]), np.array([-5., 2., 1., 2.])
    audit = r.Audit(Meter(), "source")
    arrays = arrays_for_score(raw, np.zeros(4), raw + correction, 0, neural=False)
    assert r.score_and_command(arrays, 0, "B", raw, None, False, audit, {}, correction) == 0
    assert audit.counts == {"B_committed_scores": 1}
    arrays["total_q"][0] = raw / 1200. + correction
    with pytest.raises(AssertionError, match="composition"):
        r.score_and_command(arrays, 0, "B", raw, None, True, audit, {}, correction)


def test_incomplete_student_cannot_publish_and_ordinary_has_no_NN():
    audit = r.Audit(Meter(), "source")
    raw = np.array([10., 8., 30., 40.])
    arrays = arrays_for_score(raw, np.zeros(4), np.zeros(4), -1, scored=False, neural=False)
    assert r.score_and_command(arrays, 0, "S0", raw, None, False, audit, {}, None) == 0
    with pytest.raises(AssertionError, match="eligible result"):
        r.score_and_command(arrays, 0, "S0", raw, None, True, audit, {}, None)
    assert r.score_and_command(arrays, 0, "G", raw, None, True, audit, {}, None) == 1
    arrays["score_complete"][0] = True
    with pytest.raises(AssertionError, match="placeholders"):
        r.score_and_command(arrays, 0, "R1", raw, None, True, audit, {}, None)


def terminal_rollout(monkeypatch, cap):
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (shape, dtype) in r.R_SHAPES.items()}
    for name in ("branch_action", "branch_tape", "g_links", "tape_times", "cohort_reuse", "cohort_branches"):
        arrays[name].fill(-1)
    users = np.full((50, 2), 2500, np.int32)
    positions = np.tile(np.array([2500., 2500., 100.]), (6, 1))
    state = dict(world=0, tick=1180, users=users, rates=np.array([6, 3, 2, 1], np.uint8),
                 pairs=np.arange(6, dtype=np.uint8).reshape(3, 2), positions=positions,
                 counts=np.array([1, 0, 0, 0]), progress=np.zeros(4, np.uint8),
                 slots=np.arange(6, dtype=np.uint8), ack=np.zeros(50, bool))
    for name in ("positions", "counts", "progress", "slots", "tick"):
        arrays["initial"][0][name] = state[name]
        arrays["g"][0][name] = state[name]
    arrays["initial"][0]["routes"].fill(-1)
    arrays["g"][0]["complete"] = 1
    arrays["g"][0]["costs"] = [260.] * 4
    order = np.roll(np.arange(4), -3)
    for branch, action in enumerate(order):
        arrays["rows"][branch] = 21
        arrays["branch_action"][branch], arrays["branch_tape"][branch] = action, 0
        arrays["branch_complete"][branch], arrays["branch_cost"][branch] = 1, 260.
        arrays["states"][branch, :21] = arrays["initial"][0]
        arrays["states"][branch, :21]["tick"] = np.arange(1180, 1201)
        arrays["tick_cost"][branch, :20] = 1
    key = r.wire_key(state, np.empty(0, np.int64), np.empty((0, 4), bool), "source")
    cohorts = []
    for tape in range(cap):
        arrays["tape_complete"][tape] = arrays["cohort_complete"][tape] = 1
        arrays["cohort_reuse"][tape] = -1 if tape == 0 else 0
        arrays["cohort_costs"][tape] = 260.
        arrays["cohort_branches"][tape] = np.argsort(order)
        arrays["cohort_input_sha256"][tape] = np.frombuffer(bytes.fromhex(key), np.uint8)
        arrays["cohort_ready_ns"][tape] = tape + 2
        cohorts.append(dict(tape=tape, times=[], bits=[], input_sha256=key,
                            reused_cohort=None if tape == 0 else 0,
                            branches=np.argsort(order).tolist(), costs=[260.] * 4))
    statistics = dict(initial_attempts=1, initial_complete=1, clone_attempts=4, clones=4,
                      native_attempts=80, native_complete=80, g_attempts=1, g_complete=1,
                      g_reserved_candidate_ticks=80, g_complete_candidate_ticks=80,
                      tape_attempts=cap, tape_draws=cap, cohorts_complete=cap, cohorts_reused=cap-1)
    arrays["stats"][:] = [statistics.get(name, 0) for name in r.R_STATS]
    native = dict(native_step_calls=80, native_steps=80)
    arrays["native_events"][:] = [native.get(name, 0) for name in r.c.NATIVE_EVENT_NAMES]
    selected = dict(cohorts=cohorts, timing=dict(start_ns=0, deadline_ns=20_000_000_000,
                    command_fixed_ns=10, reaped_ns=11, deadline_expired=False, completed_request=True,
                    messages=[dict(type="cohort", ready_ns=t+2, received_ns=t+3, eligible=True) for t in range(cap)]))
    calls = []
    def physics(positions, users):
        calls.append(1)
        return dict(connections=np.zeros((6, 50), bool), uav_connections=np.zeros((6, 6), bool),
                    bs_connections=np.zeros(6, bool), routes=np.full((6, 7), -1), route_lengths=np.zeros(6))
    monkeypatch.setattr(r, "physical_state", physics)
    monkeypatch.setattr(r, "future_arrivals", lambda state, tape: (np.empty(0, np.int64), np.empty((0, 4), bool)))
    monkeypatch.setattr(r, "commanded_motion", lambda pos, active, users: (None, None, pos.copy(), None))
    return arrays, state, arrays["g"][0].copy(), selected, calls


@pytest.mark.parametrize("cap", [1, 4])
def test_R_tape_cap_shared_initial_reuse_multiplicity_and_base_G_once(monkeypatch, cap):
    arrays, state, collected, selected, calls = terminal_rollout(monkeypatch, cap)
    audit = r.Audit(Meter(), "source")
    checked = r.rollout_read(arrays, state, collected, selected, audit, cap)
    assert checked["committed_cohorts"] == cap and checked["reused_cohorts"] == cap - 1
    assert len(calls) == 81 and audit.counts["R_initial_physical_states"] == 1
    assert audit.counts["R_prefix_physical_states"] == 80
    assert audit.counts["G_duplicate_R_base_records"] == 1 and "G_attempts" not in audit.counts
    assert all(item["cost"] == 260 for item in checked["branches"])


def test_R1_forbids_second_attempt_even_without_payload(monkeypatch):
    arrays, state, collected, selected, calls = terminal_rollout(monkeypatch, 1)
    arrays["stats"][r.R_STATS.index("tape_attempts")] = 2
    selected["timing"]["deadline_expired"] = True
    with pytest.raises(AssertionError, match="attempt cap"):
        r.rollout_read(arrays, state, collected, selected, r.Audit(Meter(), "source"), 1)
    assert not calls


def test_R_late_completed_unused_work_is_checked_without_selecting(monkeypatch):
    arrays, state, collected, selected, calls = terminal_rollout(monkeypatch, 1)
    selected["cohorts"] = []
    selected["timing"].update(deadline_expired=True, command_fixed_ns=20_000_000_000,
                              reaped_ns=20_000_000_010, messages=[])
    arrays["cohort_ready_ns"][0] = 20_000_000_001
    result = r.rollout_read(arrays, state, collected, selected, r.Audit(Meter(), "source"), 1)
    assert len(calls) == 81 and result["selected_cohorts"] == 0
    assert result["completed_unused_branches"] == [0, 1, 2, 3]


def test_R_copy_identity_failure_precedes_prefix_physics(monkeypatch):
    arrays, state, collected, selected, calls = terminal_rollout(monkeypatch, 1)
    arrays["states"][0, 0]["positions"][0, 0] += 1
    with pytest.raises(AssertionError, match="clone initial"):
        r.rollout_read(arrays, state, collected, selected, r.Audit(Meter(), "source"), 1)
    assert len(calls) == 1


def test_completed_T_missing_is_not_zero_and_user_gaps_include_tails():
    ledger = r.FIFO()
    ledger.arrive(0, [True, False, False, False])
    ledger.area = 1200
    ack = np.zeros((1200, 50), bool)
    ack[500, 0] = True
    result = r.extended_metrics(ledger, ack, np.zeros((1201, 6, 3)), np.zeros((1200, 6), np.uint8),
                                np.tile([1, 0, 0, 0], (1200, 1)), np.zeros((1200, 6), np.uint8))
    assert result["T_completed_max"] is None and result["T_missing_no_completions"]
    assert result["censored_residence_max_lower_bound"] == 1200 and result["W_max"] == 1200
    assert result["user_longest_service_gap"][0] == 699
    assert result["unfinished_age_lower_bounds"] == [1200]


def test_paired_missing_T_withholds_panel_without_dropping_world():
    left, right = [20.] * 32, [15.] * 32
    left[3] = None
    result = r.paired_difference(left, right, "fixed same-world panel")
    assert result["n"] == 32 and result["defined"] == 31
    assert result["mean"] is None and result["interval"] is None
    assert result["missing_worlds"] == [r.c.MAIN_WORLDS[3]]
    complete = r.paired_difference([20.] * 32, right, "fixed")
    assert complete["df"] == 31 and complete["interval"] == [5., 5.]
    assert r.paired_read([1., 2., 3.], [0, 1, 2], "three fits")["df"] == 2


def test_endpoint_arrays_independent_anchor_and_all_four_mean():
    raw = np.tile([1200., 0., 2400., 3600.], (2100, 1))
    teacher = np.tile([10., 20., 30., 40.], (2100, 1))
    residual = np.tile(np.array([-1., 0., 0., 0.], np.float32), (2100, 1))
    bank = SimpleNamespace(raw_g=raw, teacher=teacher)
    q = raw / 1200. + residual.astype(np.float64)
    errors = (q - q[:, 1, None]) - (teacher - teacher[:, 1, None]) / 1200.
    saved = dict(residual=residual, q=q, relative_errors=errors, relative_loss=np.mean(errors**2, axis=1),
                 action=np.ones(2100, np.int64), teacher_action=np.zeros(2100, np.int64),
                 regret=np.full(2100, 10.), ties=q == q.min(axis=1)[:, None],
                 teacher_ties=teacher == teacher.min(axis=1)[:, None], margin=np.zeros(2100),
                 teacher_margin=np.full(2100, 10.))
    result = r.verify_endpoint_arrays(bank, {"residual": residual}, saved)
    assert result["teacher_regret_mean"] == 10. and result["student_tied_contexts"] == 2100
    saved["relative_errors"] = errors.copy()
    saved["relative_errors"][0, 1] = 1.
    with pytest.raises(AssertionError, match="relative_errors"):
        r.verify_endpoint_arrays(bank, {"residual": residual}, saved)


def test_import_and_reader_source_have_no_eager_Torch_thread_or_optimizer_effects():
    tree = ast.parse(Path(r.__file__).read_text())
    top_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert not any((getattr(node, "module", "") or "").startswith("torch") or
                   any(name.name == "torch" for name in node.names) for node in top_imports)
    attrs = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert "set_num_threads" not in attrs and "set_num_interop_threads" not in attrs
    assert "backward" not in attrs and "step" not in attrs
    assert r.old.rollout_read is not r.rollout_read


def test_failure_summary_retains_paid_attempts_and_never_retries(tmp_path, monkeypatch):
    meter = Meter()
    def failure(root, manifest, summary, config, source, audit):
        audit.reserve("neural_attempted_rows", 4)
        raise RuntimeError("fabricated interrupted read")
    monkeypatch.setattr(r, "validate_manifest", failure)
    with pytest.raises(RuntimeError, match="interrupted read"):
        r.run(tmp_path, tmp_path / "out", SimpleNamespace(launch_sha="launch"),
              dict(worker_root=tmp_path, meter=meter, manifest={}, worker_summary={}, worker_config={}, source_identity="source"))
    result = json.loads((tmp_path / "out/summary.json").read_text())
    assert result["status"] == "FAILED" and result["checked_missions"] == 0
    assert result["counts"] == {"neural_attempted_rows": 4}
    assert len([event for event in meter.events if event[:2] == ("reserve", "reader_neural_attempted_rows")]) == 1


def test_independent_teacher_mean_preserves_unequal_alias_multiplicity(monkeypatch):
    trace, _, _, selected, _ = terminal_rollout(monkeypatch, 4)
    for tape in range(4):
        trace["cohort_costs"][tape] = np.arange(1., 5.)
        selected["cohorts"][tape]["costs"] = [1., 2., 3., 4.]
    for action, branch in enumerate(trace["cohort_branches"][0]):
        trace["branch_cost"][branch] = action + 1.
    trace["cohort_reuse"][1] = -1
    trace["cohort_input_sha256"][1] = np.full(32, 7, np.uint8)
    trace["cohort_branches"][1] = np.arange(4, 8)
    trace["cohort_costs"][1] = np.arange(9., 13.)
    trace["branch_complete"][4:8] = 1
    trace["branch_action"][4:8] = np.arange(4)
    trace["branch_tape"][4:8] = 1
    trace["branch_cost"][4:8] = np.arange(9., 13.)
    selected["cohorts"][1].update(input_sha256=bytes([7] * 32).hex(), reused_cohort=None,
                                 branches=list(range(4, 8)), costs=list(range(9, 13)))
    monkeypatch.setattr(r.acq, "cohort_mean", forbidden)
    result = r.teacher_mean(trace, selected["cohorts"])
    np.testing.assert_array_equal(result, np.arange(3., 7.))
    trace["branch_cost"][4] += 1
    with pytest.raises(AssertionError, match="outcome copies"):
        r.teacher_mean(trace, selected["cohorts"])


def test_independent_constant_scalar_system_sign_anchor_order_and_one_fake_solve(monkeypatch):
    bank = SimpleNamespace(raw_g=np.tile([20., 10., 30., 40.], (2100, 1)),
                           teacher=np.tile([25., 13., 35., 39.], (2100, 1)), identity="bank", validate=lambda: None)
    meter, calls = Meter(), []
    def solver(matrix, rhs):
        assert meter.counts["b06_constant_verification_solve_attempts"] == 1
        assert "b06_constant_verification_solves" not in meter.counts
        expected = np.array([[1., -1., 0., 0.], [-1., 3., -1., -1.],
                             [0., -1., 1., 0.], [0., -1., 0., 1.]]) * 2100
        np.testing.assert_array_equal(matrix[:4, :4], expected)
        np.testing.assert_array_equal(matrix[4], [1., 1., 1., 1., 0.])
        np.testing.assert_array_equal(matrix[:, 4], [1., 1., 1., 1., 0.])
        np.testing.assert_array_equal(rhs, [4200., 0., 4200., -8400., 0.])
        calls.append(1)
        return np.array([1., -1., 2., -2., .125], np.float64)
    monkeypatch.setattr(r.acq, "solve_constant", forbidden)
    result = r.verify_constant(bank, meter, solver=solver)
    assert calls == [1] and result["counts"]["system_action_rows"] == 8400
    assert result["counts"]["solves"] == 1 and result["constraint_residual"] == 0.
    np.testing.assert_array_equal(result["b"], [1., -1., 2., -2.])
    def failure(matrix, rhs):
        raise RuntimeError("fake solver failure")
    failed_meter = Meter()
    with pytest.raises(RuntimeError, match="solver failure"):
        r.verify_constant(bank, failed_meter, solver=failure)
    assert failed_meter.counts["b06_constant_verification_solve_attempts"] == 1
    assert "b06_constant_verification_solves" not in failed_meter.counts


def fit_evidence(tmp_path):
    prefix = tmp_path / "fits/fit0"
    prefix.mkdir(parents=True)
    initial = {"mock.weight": np.array([0., 0.], np.float32)}
    final = {"mock.weight": np.array([1., 1.], np.float32)}
    group = dict(r.c.frozen_contract()["adam"], params=[0], capturable=False, differentiable=False)
    group["betas"] = tuple(group["betas"])
    optimizer = {"param_groups": [group], "state": {0: dict(step=np.array(2112., np.float32),
                    exp_avg=np.zeros(2, np.float32), exp_avg_sq=np.ones(2, np.float32))}}
    counts = dict(scorer_constructor_attempts=1, scorer_constructors=1, update_attempts=2112, updates=2112,
                  forward_attempts=2112, forward_attempted_rows=537600, forward_calls=2112, forward_rows=537600,
                  backward_attempts=2112, backwards=2112, clip_attempts=2112, clips=2112,
                  optimizer_attempts=2112, optimizer_steps=2112)
    initial_hash, final_hash = r.typed_hash(initial), r.typed_hash(final)
    previous_parameter = initial_hash
    previous_optimizer = r.typed_hash({"state": {}, "param_groups": copy.deepcopy(optimizer["param_groups"])})
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 51, 0))))
    journal, epochs, ordinal, rows = [], [], 0, 0
    for epoch in range(64):
        permutation = rng.permutation(2100)
        for batch, start in enumerate(range(0, 2100, 64)):
            ordinal += 1
            indices = permutation[start:start+64]
            rows += 4 * len(indices)
            attempt = dict(fit=0, epoch=epoch, batch=batch, number=ordinal, batch_size=len(indices),
                           indices=indices.tolist(), parameters_before=previous_parameter,
                           optimizer_before=previous_optimizer, status="ATTEMPTED", completed=False)
            previous_parameter = final_hash if ordinal == 2112 else f"{ordinal:064x}"
            previous_optimizer = r.typed_hash(optimizer) if ordinal == 2112 else f"{ordinal+3000:064x}"
            complete = dict(attempt, status="COMPLETE", completed=True, parameters_after=previous_parameter,
                            optimizer_after=previous_optimizer, loss=.5, gradient_norm_before=20.,
                            gradient_norm_after=10.0001, cpu_seconds=.01, wall_seconds=.02,
                            counts={name: 1 if name.startswith("scorer_") else rows if name in
                                    ("forward_rows", "forward_attempted_rows") else ordinal for name in counts})
            journal.extend([attempt, complete])
        epochs.append(dict(epoch=epoch, context_weighted_online_loss=.5, contexts=2100,
                           updates=33, fixed_endpoint_evaluation=False))
    state = dict(schema=1, fit=0, init_seed=r.c.TORCH_INIT_SEEDS[0], bank_identity="bank", source_identity="source",
                 launch_sha="launch", counts=counts, optimizer=optimizer, rng=rng.bit_generator.state,
                 initial_parameter_sha256=initial_hash, final_parameter_sha256=final_hash)
    record = dict(fit=0, status="COMPLETE", bank_identity="bank", source_identity="source", launch_sha="launch",
                  counts=counts, parameter_motion=dict(l2=float(np.sqrt(2)), max=1., changed_coordinates=2))
    (prefix / "fit.json").write_text(json.dumps(record))
    (prefix / "epochs.json").write_text(json.dumps(epochs))
    (prefix / "updates.jsonl").write_text("".join(json.dumps(row) + "\n" for row in journal))
    models = {(0, "initial"): SimpleNamespace(payload={"parameters": initial}),
              (0, "final"): SimpleNamespace(payload={"parameters": final},
                                            torch=SimpleNamespace(load=lambda *args, **kwargs: copy.deepcopy(state)))}
    return record, models, state, journal


def test_saved_fit_schedule_state_chain_and_finite_norm_diagnostics_without_optimizer(tmp_path):
    record, models, state, journal = fit_evidence(tmp_path)
    audit = r.Audit(Meter(), "source")
    root = Path(r.__file__).resolve().parents[4]
    result = r.verify_fit(root, tmp_path, record, SimpleNamespace(identity="bank"), models, audit)
    assert result["updates"] == 2112 and result["training_forward_rows"] == 537600
    assert result["gradient_cap_excess_diagnostic"] > 0 and not result["optimizer_replayed"]
    assert audit.counts == {"training_state_reads": 1, "verified_update_records": 2112}
    assert journal[64]["batch_size"] == 52 and state["counts"]["forward_rows"] == 537600
    journal[0]["indices"][0] = -1
    (tmp_path / "fits/fit0/updates.jsonl").write_text("".join(json.dumps(row) + "\n" for row in journal))
    with pytest.raises(AssertionError, match="shuffle indices"):
        r.verify_fit(root, tmp_path, record, SimpleNamespace(identity="bank"), models, audit)


def test_complete_entry_mock_roster_censor_exposure_and_compact_checks(tmp_path, monkeypatch):
    records = [{"world": world, "label": label} for world, label in r.c.expected_roster()]
    def acquire(root, worker_root, context, audit):
        audit.counts.update(neural_rows=50400, bank_neural_rows=50400)
        return {}, np.zeros(4), {"pure_mock": True}
    def mission(record, worker_root, manifest, audit, models, constant):
        audit.add("native_physical_states", 1201)
        audit.add("native_motion_steps", 1200)
        audit.add("missions")
        arm = record["label"].split("/")[-1]
        if arm.startswith("S"):
            audit.add("neural_rows", 4)
            audit.add("deployment_neural_rows", 4)
        return dict(record, arm=arm, committed_neural_decisions=int(arm.startswith("S")),
                    rollout_checks=[{}] * (60 if arm.startswith("R") else 0), deadline_misses=1)
    endpoints = [dict(name=arm, counts=dict(frozen_nn_rows=256 if arm.startswith("S") else 0,
                 frozen_nn_attempted_rows=260 if arm.startswith("S") else 0, constant_scores=0)) for arm in r.c.ARMS]
    monkeypatch.setattr(r, "validate_manifest", lambda *args: records)
    monkeypatch.setattr(r, "acquire_checks", acquire)
    monkeypatch.setattr(r, "read_mission", mission)
    monkeypatch.setattr(r, "compare_panel", lambda *args: {"pure_mock": True})
    context = dict(worker_root=tmp_path, meter=Meter(), manifest={"endpoint_counts": endpoints},
                   worker_summary={"launch_sha": "worker"}, worker_config={}, source_identity="source")
    r.run(tmp_path, tmp_path / "out", SimpleNamespace(launch_sha="reader"), context)
    result = json.loads((tmp_path / "out/summary.json").read_text())
    assert result["status"] == "COMPLETE" and result["counts"]["native_physical_states"] == 269024
    assert len(list((tmp_path / "out/checks").rglob("*.json"))) == 224
    exposure = result["deployment_neural_exposure"]["S0"]
    assert exposure["completed_rows_without_committed_cache"] == 128
    assert exposure["attempted_rows_without_completed_forward"] == 4


def test_manifest_byte_binding_roster_mirrors_and_corruption(tmp_path):
    config = dict(source_identity="source", launch_sha="launch", mode="worker", seed=r.c.MASTER_SEED,
                  contract=r.c.frozen_contract())
    records = [dict(world=world, label=label, status="COMPLETE", completed_native_steps=1200,
                    npz=f"raw/{label}/{world}.npz", metadata=f"raw/{label}/{world}.json")
               for world, label in r.c.expected_roster()]
    files = {"config.json", "endpoint-counts.json", "constant.json", "bank.npz", "bank-provenance.json"}
    files.update(record[key] for record in records for key in ("npz", "metadata"))
    for fit in range(3):
        files.update(f"fits/fit{fit}/" + name for name in (f"fit{fit}_initial.pt", f"fit{fit}_final.pt",
                     f"fit{fit}_training.pt", "initial-bank.npz", "final-bank.npz", "updates.jsonl", "epochs.json", "fit.json"))
    for relative in files:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fabricated bytes only")
    (tmp_path / "config.json").write_text(json.dumps(config))
    (tmp_path / "endpoint-counts.json").write_text("[]")
    manifest = dict(schema=1, records=records, files={name: r.acq.file_identity(tmp_path/name) for name in files},
                    fits=[dict(fit=i) for i in range(3)], endpoint_counts=[])
    summary = dict(schema=1, status="COMPLETE", object=r.c.OBJECT, missions=224, source_identity="source",
                   launch_sha="launch", fits=manifest["fits"], endpoint_counts=[], acquisition_totals=dict(
                       constant_fits=1, neural_fits=3, updates=6336, backwards=6336, context_presentations=403200,
                       training_neural_rows=1612800, bank_endpoint_neural_rows=50400))
    audit = r.Audit(Meter(), "source")
    assert r.validate_manifest(tmp_path, manifest, summary, config, "source", audit) == records
    assert audit.counts["file_hashes"] == len(files)
    (tmp_path / "bank.npz").write_bytes(b"corrupt")
    with pytest.raises(AssertionError, match="artifact hash bank.npz"):
        r.validate_manifest(tmp_path, manifest, summary, config, "source", audit)


def test_comparison_shared_world_covariance_missing_T_and_CPU_cost_scopes(tmp_path):
    costs = dict(G=2., R4=5., R1=3., B=1.5, S0=1., S1=2., S2=6.)
    rows = []
    for world in r.c.MAIN_WORLDS:
        for arm in r.c.ARMS:
            metrics = {name: 10. for name in r.METRICS}
            metrics["T_completed_max"] = None if arm == "S0" and world == r.c.MAIN_WORLDS[0] else 10.
            rows.append(dict(metrics, arm=arm, world=world, cost=dict(inclusive_cpu_seconds=costs[arm]),
                             first_public_identity="same", first_cohort_identity="same"))
    constant_path = tmp_path / "constant.json"
    constant_path.write_text(json.dumps({"acquisition_cost": dict(cpu_seconds=3., wall_seconds=4., scope="B fit")}))
    manifest = dict(constant={"path": str(constant_path)}, fits=[dict(acquisition_cost=dict(
                     cpu_seconds=10.+fit, wall_seconds=12., scope="one fit")) for fit in range(3)])
    summary = dict(bank_handling_cost=dict(cpu_seconds=2., wall_seconds=3., scope="shared bank"),
                   acquisition_cost=dict(cpu_seconds=40., wall_seconds=50., scope="whole acquisition"),
                   cost=dict(phase_cpu_seconds=1000.))
    comparison = r.compare_panel(rows, manifest, summary, Meter())
    assert comparison["contrasts"]["R1-R4"]["C"]["df"] == 31
    fits = comparison["fit_conditional_summaries"]["G"]["C"]
    assert fits["three_fit_means"]["df"] == 2 and fits["shared_world_student_average"]["df"] == 31
    assert comparison["contrasts"]["S0-G"]["T_completed_max"]["interval"] is None
    assert comparison["whole_new_research_CPU_intercept_counted_once"] == 100.
    curves = {(row["fit"], row["baseline"]): row for row in comparison["cpu_crossings"]}
    assert curves[0, "B"]["marginal_shared_bank_plus_one_fit_cpu"] == 12.
    assert curves[0, "B"]["comparator_acquisition_cpu"] == 5.
    assert curves[0, "B"]["incremental_crossing_uses"] == 14.
    assert curves[0, "G"]["whole_study_crossing_uses"] == 100.
    assert curves[1, "G"]["marginal_crossing_uses"] is None
    assert curves[2, "R4"]["whole_study_crossing_uses"] is None
    assert comparison["old_teacher_unknown_extra_acquisition_and_reader_cost"]


def test_complete_mission_saved_timeline_with_mock_world_physics_G_and_RNG(tmp_path, monkeypatch):
    """Exercise full reader chronology; every effect provider is a fixed mock."""
    arrays = {name: np.zeros(shape, dtype=dtype) for name, (shape, dtype) in r.MISSION_SHAPES.items()}
    slots = np.arange(6, dtype=np.uint8)
    command = np.array([1, 0, 2, 3, 4, 5], np.uint8)
    rates = np.array([6, 3, 2, 1], np.uint8)
    arrays["users"][:] = 0
    arrays["rates"][:] = rates
    arrays["pairs"][:] = np.arange(6).reshape(3, 2)
    arrays["initial_slots"][:] = slots
    arrays["arrival_draws"][:] = 1.
    arrays["states"]["tick"] = np.arange(1201)
    arrays["states"]["slots"][:21] = slots
    arrays["states"]["slots"][21:] = command
    arrays["states"]["routes"].fill(-1)
    arrays["reports"]["tick"] = np.arange(60) * 20
    arrays["reports"]["slots"][0] = slots
    arrays["reports"]["slots"][1:] = command
    arrays["reports"]["complete"] = 1
    arrays["reports"]["costs"][:] = [2., 1., 0., 3.]
    arrays["g_action"][:] = arrays["action"][:] = 2
    arrays["greedy_action"][:] = -1
    arrays["commands"][:] = command
    native = dict.fromkeys(r.c.NATIVE_EVENT_NAMES, 0)
    native.update(constructor_calls=1, reset_calls=1, registry_calls=1, native_step_calls=1200,
                  native_steps=1200, dense_reward_entries=2400, parent_reward_entries=2400,
                  constructor_topology_restorations=1)
    timing = dict(start_ns=0, deadline_ns=20_000_000_000, command_fixed_ns=2, reaped_ns=3,
                  deadline_expired=False, completed_request=True, cpu_seconds=.01,
                  messages=[dict(type="result", ready_ns=1, received_ns=2, eligible=True)])
    metadata = dict(schema=1, status="COMPLETE", world=0, label="main/G", training=False, initial_audit=False,
                    completed_native_steps=1200, completed_decisions=60, last_command_unused=True,
                    actual_native_events=native, decisions=[dict(score_complete=False, timing=timing, cohorts=[]) for _ in range(60)],
                    rollout_traces=[], requests=[], completions=[], unfinished=[[], [], [], []], total_cost=0,
                    area_cost=0, terminal_charge=0, logical_reset_bytes=404, logical_report_bytes=61*171,
                    logical_command_bytes=360, logical_training_feedback_bytes=0,
                    cost=dict(inclusive_cpu_seconds=1., inclusive_wall_seconds=2.,
                              before=dict(phase_cpu_seconds=0.), after=dict(phase_cpu_seconds=1.)))
    monkeypatch.setattr(r, "load_arrays", lambda *args: arrays)
    monkeypatch.setattr(r, "read_json", lambda *args: metadata)
    monkeypatch.setattr(r, "geometry", lambda world: (np.zeros((6, 3)), np.zeros((50, 2), np.int32)))
    monkeypatch.setattr(r, "assignment", lambda *args: (slots.copy(), arrays["pairs"].copy()))
    monkeypatch.setattr(r, "features", lambda *args: np.zeros((4, 303), np.float32))
    monkeypatch.setattr(r, "slots_for", lambda users: np.zeros((6, 3)))
    monkeypatch.setattr(r, "candidates", lambda state: np.array([slots, slots, command, slots]))
    monkeypatch.setattr(r, "lawful", lambda *args: None)
    monkeypatch.setattr(r, "motion", lambda positions, raw: (raw.copy(), positions.copy(), None))
    monkeypatch.setattr(r, "predict_g", lambda state: (np.array([2., 1., 0., 3.]), min(240, 1200-state["tick"]), 0))
    monkeypatch.setattr(r, "physical_state", lambda *args: dict(connections=np.zeros((6, 50), bool),
                    uav_connections=np.zeros((6, 6), bool), bs_connections=np.zeros(6, bool),
                    routes=np.full((6, 7), -1), route_lengths=np.zeros(6)))
    monkeypatch.setattr(r.np.random, "Generator", lambda *args: SimpleNamespace(
                    permutation=lambda values: rates.copy(), random=lambda shape: np.ones(shape)))
    audit = r.Audit(Meter(), "source")
    record = dict(world=0, label="main/G", npz="mock.npz", metadata="mock.json", total_cost=0)
    result = r.read_mission(record, tmp_path, {}, audit, {}, None)
    assert result["C"] == 0 and result["empty_workload"] and result["T_completed_max"] is None
    assert audit.counts["native_physical_states"] == 1201 and audit.counts["G_queries"] == 60
    assert result["active_uav_target_changes"] == 2
    arrays["states"][20]["slots"] = command
    with pytest.raises(AssertionError, match="exact20-tick target delay"):
        r.read_mission(record, tmp_path, {}, r.Audit(Meter(), "source"), {}, None)
