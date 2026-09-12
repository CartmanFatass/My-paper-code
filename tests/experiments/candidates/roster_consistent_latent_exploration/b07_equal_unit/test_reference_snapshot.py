"""Deterministic native-struct/caller fixtures; no model, native kernel or RNG."""
import ctypes
from dataclasses import fields
from types import SimpleNamespace

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import native_backend as native
from test_update import ROOT, SOURCE, MemoryPath, definition


@pytest.mark.parametrize("count", [6, 8, 10, 12])
def test_eager_copy_matches_lazy_fields_and_owns_roster_values(count):
    raw = native._Snapshot()
    raw.agent_count, raw.tick = count, 24
    raw.claim_required, raw.roster_event = 1, 1
    raw.last_u, raw.last_fragmentation, raw.tau = -1, -1, -1
    for index in range(count):
        raw.positions[index] = index * 2
        raw.transport_keys[index] = index + 10
        raw.angular_ranks[index] = index
    eager, lazy = native._snapshot(raw), native._NativeSnapshotView(raw)
    for field in fields(eager):
        assert getattr(eager, field.name) == getattr(lazy, field.name)
    saved = eager.positions, eager.transport_keys
    raw.positions[0], raw.transport_keys[0] = 99, 99
    assert (eager.positions, eager.transport_keys) == saved
    assert len(eager.positions) == len(eager.transport_keys) == count


def test_alignment_failure_keeps_guard_and_reports_actual_columns():
    batch = native.NativeBatch.__new__(native.NativeBatch)
    batch._closed = False
    batch._handles = (ctypes.c_void_p * 1)()
    batch._raw_snapshots = (native._Snapshot * 1)()
    batch._raw_snapshots[0].agent_count, batch._raw_snapshots[0].tick = 8, 24
    batch._snapshots = (native._snapshot(batch._raw_snapshots[0]),)
    with pytest.raises(ValueError, match="lane=0 tick=24 positions=8 keys=8 previous=7 survivors=8 raw_count=8"):
        batch.scripted_actions(0, [(-1,) * 7], [(False,) * 8], [True], [True], [0])


@pytest.mark.parametrize("packed", [True, False])
def test_reference_evaluator_passes_selected_representation_to_same_batch(packed):
    calls = []
    rng = SimpleNamespace(_native_binding="same-binding")
    snapshot = SimpleNamespace(terminal=True, tau=40, U=.2, F=.1)
    batch = SimpleNamespace(snapshots=(snapshot,) * 8, closed=False, close=lambda: None)

    def reset(fixtures, **kwargs):
        calls.append(kwargs)
        return batch

    namespace = dict(Sequence=object, SemanticRNG=object, EpisodeCoordinate=object,
                     ScriptedEpisodeResult=lambda *v: v, SCRIPTED_PACKAGES=("NEAREST",),
                     SUPPORTED_BATCH_WIDTHS=(8,), EmpiricalRunnerError=RuntimeError,
                     _require_semantic_rng=lambda r: SimpleNamespace(require_runtime_authority=lambda: None),
                     materialize_fixture_batch=lambda *a: ("fixture",) * 8, reset_native_batch=reset)
    # Postponed annotations are only syntax here; the function uses no type values.
    import ast
    path = ROOT / "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py"
    node = next(n for n in ast.parse(path.read_text(encoding="utf-8")).body if getattr(n, "name", None) == "execute_scripted_batch")
    module = ast.fix_missing_locations(ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    coordinates = tuple(SimpleNamespace(update_or_scenario=i) for i in range(8))
    eval_namespace = dict(SemanticRNG=object, INDEPENDENT_NEAREST="NEAREST", HELDOUT_CELLS=("cell",),
                          heldout_batches=lambda *a: (coordinates,), execute_scripted_batch=namespace["execute_scripted_batch"],
                          scenario_row=lambda cell, index, arm, episode: dict(cell=cell, index=index, arm=arm, result=episode))
    evaluate = definition(ROOT / "experiments/candidates/roster_consistent_latent_exploration_tbcfv_b01/study.py", "evaluate_scripted", eval_namespace)
    result = evaluate(rng, 256, packed_views=packed)
    assert len(result) == 8
    assert calls == [dict(packed_views=packed, binding="same-binding")]
    assert all(row["arm"] == "NEAREST" for row in result)


@pytest.mark.parametrize("packed", [True, False])
def test_shared_reference_output_keeps_legacy_default_and_marks_opt_in(packed):
    calls, writes = [], {}
    def evaluate(rng, count, **kwargs):
        calls.append((count, kwargs))
        return []
    host = SimpleNamespace(evaluate_scripted=evaluate, seed_root_key=lambda s: b"fixture",
                           load_control_summary=lambda p: dict(initialization_panel=[], scenarios=[]),
                           check_wall=lambda *a: None, peak_rss_bytes=lambda: 0,
                           write_json=lambda p, value: writes.update({str(p): value}),
                           ArmWallExpired=type("ArmWallExpired", (Exception,), {}))
    namespace = dict(SEED=24, UPDATES=200, OBJECT_ID="legacy", LAW={}, host=host,
                     time=SimpleNamespace(perf_counter=lambda: 1),
                     traceback=SimpleNamespace(print_exc=lambda: None),
                     b03=SimpleNamespace(panel_summary=lambda rows: {}),
                     make_rng=lambda *a, **k: (SimpleNamespace(root_digest="fixture", certificate={"native": {}}), object()),
                     comparisons=lambda *a: dict(primary=dict(Delta_ref=0, G_U=0, active_paths=[dict(Delta_ref=0)]), cells={}),
                     reading=lambda *a: [])
    run = definition(SOURCE / "b04_nearest_prior/study.py", "run", namespace)
    result = run("reference", MemoryPath("memory/reference"), "sha", "admission", 0, 15,
                 reference_packed_views=packed)
    assert result["status"] == "COMPLETE"
    assert calls == [(256, {} if packed else dict(packed_views=False))]
    assert ("reference_packed_views" in result) is (not packed)
    assert writes["memory/reference/summary.json"] == result


def test_b07_selects_eager_reference_without_changing_training_counts():
    calls = []
    namespace = dict(SEED=27, UPDATES=1000, OBJECT_ID="B07", LAW={"nearest_probability": .99},
                     training_update=object(), b04=SimpleNamespace(run=lambda *a, **kw: calls.append(kw)))
    run = definition(SOURCE / "b07_equal_unit/study.py", "run", namespace)
    run("reference", "out", "sha", "admission", 0, 12, "existing-learned")
    assert calls[0]["reference_packed_views"] is False
    assert calls[0]["updates"] == 1000
    assert calls[0]["equal_unit_update"] is namespace["training_update"]
