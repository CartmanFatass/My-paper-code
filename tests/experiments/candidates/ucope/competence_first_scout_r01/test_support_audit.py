from fractions import Fraction
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.ucope.competence_first_scout_r01.contract import RunBinding, ScoutConfig
from experiments.candidates.ucope.competence_first_scout_r01.rng import rng_contract
from experiments.candidates.ucope.competence_first_scout_r01.support_audit import (
    ACCEPTED_BINDING,
    EFFECT_COUNTERS,
    EVEN_PERIODS,
    ODD_PERIODS,
    AuditBinding,
    AuditResourceMonitor,
    _ProcessSample,
    _probe_refresh_rows,
    _load_policy_checkpoint,
    DURABLE_CAP_BYTES,
    RSS_CAP_BYTES,
    RESOURCE_SAMPLE_SECONDS,
    SCRATCH_CAP_BYTES,
    WALL_CAP_SECONDS,
    _validate_resources,
    audit_complete_tree,
    build_restricted_oracle,
    choose_route,
    fraction_record,
    materially_dominates,
    median_fraction,
    policy_competence,
    score_policy_states,
    score_state,
    same_arm_odd_recast,
    snapshot_input_tree,
    validate_admission,
    validate_fresh_admission,
    validate_even_match,
    execute_audit_to_output,
    frozen_definitions,
    snapshot_implementation_sources,
    validate_audit_artifact,
    validate_audit_core,
    validate_direct_scored_row,
    validate_implementation_source_snapshots,
)
from scripts import run_ucope_b1_odd_support_audit_r01 as audit_cli
from experiments.candidates.ucope.competence_first_scout_r01 import support_audit as audit_module


def test_exact_oracle_and_fraction_serialization_are_period_parameterized():
    oracle = build_restricted_oracle(ODD_PERIODS)
    assert len(oracle) == 8
    assert {row["baseline_period"] for row in oracle.values()} == {5}
    assert {tuple(row["periods"]) for row in oracle.values()} == {ODD_PERIODS}
    assert {tuple(row["baseline"].items()) for row in oracle.values()} == {
        tuple({"numerator": 157, "denominator": 200, "decimal": 0.785}.items())
    }
    assert fraction_record(Fraction(-3, 20)) == {
        "numerator": -3, "denominator": 20, "decimal": -0.15,
    }
    first = next(iter(oracle.values()))
    assert set(first["immediate_candidate_values"]) == {"1", "3", "5", "7", "9"}
    assert all(
        set(tail["candidate_values"]) == {"1", "3", "5", "7", "9"}
        for tail in first["tail"].values()
    )
    definitions = frozen_definitions()
    assert definitions["route_order"][0:2] == ["ORACLE_NONUNIQUE_TO_MAP", "ODD_RECAST_SAME_ARM"]
    assert definitions["resource_caps"]["processes"] == definitions["resource_caps"]["workers"] == 1
    assert definitions["material_dominance"]["material_delta"]["max_regret"]["numerator"] == 1


def test_stateless_bc_forward_reads_tensors_without_model_or_optimizer():
    torch = pytest.importorskip("torch")
    state = {"beta": torch.tensor([1.0, 2.0, -1.0], dtype=torch.float32)}
    z = torch.tensor([[1.0, 3.0, 2.0], [1.0, -1.0, 4.0]], dtype=torch.float32)
    x = torch.zeros((2, 9), dtype=torch.float32)
    versions = {name: tensor._version for name, tensor in state.items()}
    assert score_state(state, x, z) == (5.0, -5.0)
    assert versions == {name: tensor._version for name, tensor in state.items()}


def test_stateless_flex_forward_accepts_the_exact_frozen_tensor_inventory():
    torch = pytest.importorskip("torch")
    state = {
        "beta": torch.zeros(7, dtype=torch.float32),
        "residual.0.weight": torch.zeros((64, 9), dtype=torch.float32),
        "residual.0.bias": torch.ones(64, dtype=torch.float32),
        "residual.2.weight": torch.zeros((64, 64), dtype=torch.float32),
        "residual.2.bias": torch.ones(64, dtype=torch.float32),
        "residual.4.weight": torch.ones((1, 64), dtype=torch.float32),
        "residual.4.bias": torch.tensor([2.0], dtype=torch.float32),
    }
    x = torch.zeros((1, 9), dtype=torch.float32)
    z = torch.zeros((1, 7), dtype=torch.float32)
    assert score_state(state, x, z) == (66.0,)


def test_dominance_median_and_route_precedence_use_exact_frozen_thresholds():
    better = (0, Fraction(1, 100), Fraction(19, 20))
    worse = (1, Fraction(3, 100), Fraction(9, 10))
    assert materially_dominates(better, worse) is True
    assert materially_dominates(worse, better) is False
    assert median_fraction([Fraction(value) for value in (1, 9, 3, 7, 5, 11)]) == 6
    predicates = {
        "oracle_unique": True,
        "odd_recast": True,
        "ft_flex_over_bc": True,
        "ft_bc_over_flex": False,
        "mt_ft_root_separation": False,
        "all_similar_odd_failure": False,
    }
    assert choose_route(predicates)["route"] == "RECAST_ODD_TO_EVEN_GENERALIZATION"
    conflicting_after_recast = dict(predicates, ft_bc_over_flex=True, mt_ft_root_separation=True)
    assert choose_route(conflicting_after_recast)["route"] == "RECAST_ODD_TO_EVEN_GENERALIZATION"
    predicates["odd_recast"] = False
    assert choose_route(predicates)["route"] == "PERMIT_PAIRED_B_OPTIMIZATION_CONDITIONING_DISCRIMINATOR"
    predicates.update(ft_flex_over_bc=False, mt_ft_root_separation=True)
    assert choose_route(predicates)["route"] == "LATER_TARGET_SCHEDULE_B_COMPARISON_JUSTIFIED"
    predicates.update(mt_ft_root_separation=False, all_similar_odd_failure=True)
    assert choose_route(predicates)["route"] == "PARK_DIRECTION_PER_EXISTING_PRO_MAP"
    predicates.update(oracle_unique=False)
    assert choose_route(predicates)["route"] == "MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED"


def test_odd_recast_compares_each_odd_arm_to_the_same_retained_even_arm():
    categories = [
        {"arm_id": "MT-XF-FLEX", "competent": True, "near": True},
        {"arm_id": "FT-XF-FLEX", "competent": False, "near": False},
        {"arm_id": "FT-XF-BC", "competent": False, "near": False},
    ]
    assert same_arm_odd_recast(categories, {
        "MT-XF-FLEX": False, "FT-XF-FLEX": True, "FT-XF-BC": True,
    }) is True
    assert same_arm_odd_recast(categories, {
        "MT-XF-FLEX": True, "FT-XF-FLEX": False, "FT-XF-BC": False,
    }) is False


def test_admission_and_fixed_binding_are_fail_closed(tmp_path):
    receipt = tmp_path / "admit.json"
    minimal = {
        "schema_version": 1,
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
        "captured_at": "2026-09-01T00:00:00Z",
        "assessed_at": "2026-09-01T00:00:01Z",
    }
    receipt.write_text(json.dumps(minimal), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        validate_admission(receipt)
    payload = _central_admission_payload()
    receipt.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    assert validate_admission(receipt)["provenance"]["producer"] == "scripts/hmasd_resource_preflight.py:admit-memory"
    payload["effective_available_bytes"] = 4 * 1024**3 - 1
    receipt.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    with pytest.raises(ValueError, match="4 GiB"):
        validate_admission(receipt)
    assert ACCEPTED_BINDING.checkpoint_count == 72
    assert set(EFFECT_COUNTERS.values()) == {0}
    assert ScoutConfig.b1().root_updates == 320


def _central_admission_payload():
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "captured_at": now,
        "assessed_at": now,
        "measurement_source": "GlobalMemoryStatusEx",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 5 * 1024**3,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None,
        "effective_available_bytes": 5 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }


def _fresh_admission(tmp_path):
    receipt = tmp_path / "fresh-admission.json"
    receipt.write_bytes(
        (json.dumps(_central_admission_payload(), indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return receipt


def test_fresh_admission_rejects_stale_timestamp(tmp_path):
    receipt = _fresh_admission(tmp_path)
    assert validate_fresh_admission(receipt)["passed"] is True
    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["assessed_at"] = "2020-01-01T00:00:00Z"
    receipt.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    with pytest.raises(ValueError, match="not fresh|interval"):
        validate_fresh_admission(receipt)


def test_resource_monitor_and_caps_are_direct_and_fail_closed(tmp_path, monkeypatch):
    samples = iter((
        (_ProcessSample((1, 1), 100, 10.0, 20, 30, 40, 2),),
        (_ProcessSample((1, 1), 200, 12.0, 25, 37, 51, 3),),
        (_ProcessSample((1, 1), 150, 12.5, 26, 38, 52, 2),),
    ))
    monkeypatch.setattr(
        "experiments.candidates.ucope.competence_first_scout_r01.support_audit._process_tree_samples",
        lambda: next(samples),
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    durable = tmp_path / "durable"
    durable.mkdir()
    monitor = AuditResourceMonitor(
        scratch, durable_root=durable, sample_seconds=RESOURCE_SAMPLE_SECONDS,
    ).start()
    (scratch / "work.bin").write_bytes(b"x" * 17)
    pre_tail = monitor.snapshot()
    observed = monitor.finish()
    assert pre_tail["peak_rss_bytes"] == 200
    assert pre_tail["scratch_peak_bytes"] == 17
    assert pre_tail["peak_process_count"] == pre_tail["worker_count"] == 1
    assert pre_tail["cpu_seconds"] == pytest.approx(2.0)
    assert pre_tail["io_read_bytes"] == 5
    assert pre_tail["io_write_bytes"] == 7
    assert pre_tail["io_other_bytes"] == 11
    assert pre_tail["aggregate_io_bytes"] == 23
    assert pre_tail["sample_interval_seconds"] == RESOURCE_SAMPLE_SECONDS == 0.02
    assert pre_tail["durable_peak_bytes"] == 0
    assert observed["measurement_complete"] is True
    validated = _validate_resources(pre_tail, durable_peak_bytes=23)
    assert validated["caps"] == {
        "wall_seconds": WALL_CAP_SECONDS,
        "peak_rss_bytes": RSS_CAP_BYTES,
        "scratch_peak_bytes": SCRATCH_CAP_BYTES,
        "durable_peak_bytes": DURABLE_CAP_BYTES,
        "peak_process_count": 1,
        "peak_thread_count": 256,
        "worker_count": 1,
        "device": "cpu",
    }
    with pytest.raises(ValueError, match="cap exceeded"):
        _validate_resources({**pre_tail, "peak_rss_bytes": RSS_CAP_BYTES + 1}, durable_peak_bytes=23)
    with pytest.raises(ValueError, match="topology"):
        _validate_resources({**pre_tail, "peak_process_count": 2, "worker_count": 2}, durable_peak_bytes=23)
    with pytest.raises(ValueError, match="resource|measurement"):
        _validate_resources({**pre_tail, "sample_interval_seconds": 9.99}, durable_peak_bytes=23)
    with pytest.raises(ValueError, match="resource|measurement"):
        _validate_resources({**pre_tail, "durable_peak_bytes": 1}, durable_peak_bytes=23)
    missing_io = dict(pre_tail)
    missing_io.pop("aggregate_io_bytes")
    with pytest.raises(ValueError, match="structure"):
        _validate_resources(missing_io, durable_peak_bytes=23)


def test_odd_policy_scoring_is_stateless_exact_and_reports_full_maps():
    torch = pytest.importorskip("torch")
    root_state = {"beta": torch.tensor([0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 0.0], dtype=torch.float32)}
    tail_state = {"beta": torch.tensor([0.0, 0.0, -1.0, 0.0, 0.0], dtype=torch.float32)}
    identity = {
        "arm_id": "FT-XF-BC", "seed_id": "ucope-scout-r01-b1-fresh-00",
        "fold_id": 0, "root_update": 320,
    }
    before = {"root": root_state["beta"].clone(), "tail": tail_state["beta"].clone()}
    row = score_policy_states(root_state, tail_state, ODD_PERIODS, identity)
    assert row["identity"] == identity
    assert len(row["root_scores"]) == 8 and len(row["tail_scores"]) == 8
    assert set(next(iter(row["root_scores"].values()))) == {
        "PROBE", "IMMEDIATE:1", "IMMEDIATE:3", "IMMEDIATE:5", "IMMEDIATE:7", "IMMEDIATE:9",
    }
    assert set(row["root_selected_labels"].values()) == {"PROBE"}
    assert {period for by_count in row["tail_periods"].values() for period in by_count.values()} == {1}
    assert row["all_finite"] is True and row["all_unique"] is True
    assert row["max_regret"]["numerator"] >= 0
    assert torch.equal(before["root"], root_state["beta"])
    assert torch.equal(before["tail"], tail_state["beta"])

    row["checkpoint"] = {
        "locator": "checkpoints/FT-XF-BC/ucope-scout-r01-b1-fresh-00/fold-0/root-0320.pt",
        "size_bytes": 1,
        "sha256": "0" * 64,
    }
    row["root_scores"]["EXTRA_CONTEXT"] = dict(next(iter(row["root_scores"].values())))
    with pytest.raises(ValueError, match="context inventory"):
        validate_direct_scored_row(row, ODD_PERIODS)


def test_even_rescore_requires_every_retained_score_and_selection_exactly():
    torch = pytest.importorskip("torch")
    root_state = {"beta": torch.tensor([0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 0.0], dtype=torch.float32)}
    tail_state = {"beta": torch.tensor([0.0, 0.0, -1.0, 0.0, 0.0], dtype=torch.float32)}
    identity = {
        "arm_id": "FT-XF-BC", "seed_id": "ucope-scout-r01-b1-fresh-00",
        "fold_id": 0, "root_update": 320,
    }
    row = score_policy_states(root_state, tail_state, EVEN_PERIODS, identity)
    retained = {
        **identity,
        "all_finite": row["all_finite"], "all_unique": row["all_unique"],
        "root_actions": row["root_actions"], "root_selected_labels": row["root_selected_labels"],
        "tail_periods": row["tail_periods"], "root_scores": row["root_scores"],
        "tail_scores": row["tail_scores"], "oracle_root_match": row["oracle_root_match"],
        "max_regret": row["max_regret"]["decimal"],
        "minimum_tail_agreement": row["minimum_tail_agreement"]["decimal"],
        "competence_pass": policy_competence(row),
    }
    assert validate_even_match(row, retained)["match"] is True
    tampered = json.loads(json.dumps(retained))
    cell = next(iter(tampered["root_scores"]))
    tampered["root_scores"][cell]["PROBE"] += 1.0
    with pytest.raises(ValueError, match="even rescore mismatch"):
        validate_even_match(row, tampered)
    competence_tampered = json.loads(json.dumps(retained))
    competence_tampered["competence_pass"] = not competence_tampered["competence_pass"]
    with pytest.raises(ValueError, match="competence_pass"):
        validate_even_match(row, competence_tampered)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _synthetic_complete(tmp_path):
    torch = pytest.importorskip("torch")
    complete = tmp_path / "complete"
    complete.mkdir(parents=True)
    config = ScoutConfig.b1()
    run_binding = RunBinding.b1(
        manifest_digest="1" * 64, source_aggregate="2" * 64,
        assessment_digest="3" * 64,
    ).to_dict()
    root_bc = {"beta": torch.tensor([0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 0.0], dtype=torch.float32)}
    tail_bc = {"beta": torch.tensor([0.0, 0.0, -1.0, 0.0, 0.0], dtype=torch.float32)}

    def flex_state(beta):
        return {
            "beta": beta,
            "residual.0.weight": torch.zeros((64, 9), dtype=torch.float32),
            "residual.0.bias": torch.zeros(64, dtype=torch.float32),
            "residual.2.weight": torch.zeros((64, 64), dtype=torch.float32),
            "residual.2.bias": torch.zeros(64, dtype=torch.float32),
            "residual.4.weight": torch.zeros((1, 64), dtype=torch.float32),
            "residual.4.bias": torch.zeros(1, dtype=torch.float32),
        }

    def checkpoint_activity(arm, fold, update, tail_updates):
        frozen = arm.startswith("FT-")
        return {
            "root_inventory": config.episodes_per_context * 4,
            "tail_inventory": config.episodes_per_context * 2,
            "root_optimizer_updates": update,
            "tail_optimizer_updates": tail_updates,
            "root_example_exposures": update * config.batch_size,
            "tail_example_exposures": tail_updates * config.batch_size,
            "target_refresh_events": update if arm == "MT-XF-FLEX" else 0,
            "target_refresh_rows": _probe_refresh_rows(config, fold, update) if arm == "MT-XF-FLEX" else 0,
            "target_materialization_events": int(frozen),
            "target_materialization_rows": config.episodes_per_context * 4 if frozen else 0,
            "root_clipping_events": 0, "tail_clipping_events": 0,
            "root_gradient_norm_sum": 0.0, "tail_gradient_norm_sum": 0.0,
            "root_gradient_norm_max": 0.0, "tail_gradient_norm_max": 0.0,
            "nonfinite_events": 0,
        }

    records, evaluations = [], []
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                for update in config.evaluation_root_updates:
                    identity = {"arm_id": arm, "seed_id": seed, "fold_id": fold, "root_update": update}
                    root_state = root_bc if arm == "FT-XF-BC" else flex_state(root_bc["beta"])
                    tail_state = tail_bc if arm == "FT-XF-BC" else flex_state(tail_bc["beta"])
                    payload = {
                        "format": "UCOPE_SCOUT_R01_POLICY_CHECKPOINT_V1", "schema_version": 1,
                        "object_id": "UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01",
                        "config": config.to_dict(), "run_binding": run_binding,
                        "arm_id": arm, "seed_id": seed, "fold_id": fold,
                        "root_updates": update,
                        "tail_updates": update // 2 if arm == "MT-XF-FLEX" else config.tail_updates,
                        "activity": checkpoint_activity(
                            arm, fold, update,
                            update // 2 if arm == "MT-XF-FLEX" else config.tail_updates,
                        ),
                        "rng": rng_contract(),
                        "root_state": root_state, "tail_state": tail_state,
                        "root_optimizer_state": {}, "tail_optimizer_state": {},
                        "frozen_root_targets": None if arm == "MT-XF-FLEX" else torch.zeros(config.episodes_per_context * 4),
                    }
                    locator = f"checkpoints/{arm}/{seed}/fold-{fold}/root-{update:04d}.pt"
                    path = complete / locator
                    path.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(payload, path)
                    records.append({
                        **identity, "format": "UCOPE_SCOUT_R01_CHECKPOINT_INVENTORY_V1",
                        "locator": locator, "size_bytes": path.stat().st_size, "sha256": _sha(path),
                    })
                    even = score_policy_states(root_state, tail_state, EVEN_PERIODS, identity)
                    evaluations.append({
                        **identity, "all_finite": even["all_finite"], "all_unique": even["all_unique"],
                        "root_actions": even["root_actions"], "root_selected_labels": even["root_selected_labels"],
                        "tail_periods": even["tail_periods"], "root_scores": even["root_scores"],
                        "tail_scores": even["tail_scores"], "oracle_root_match": even["oracle_root_match"],
                        "max_regret": even["max_regret"]["decimal"],
                        "minimum_tail_agreement": even["minimum_tail_agreement"]["decimal"],
                        "competence_pass": False,
                        "acquisition_evaluations": 999,
                    })
    result = {
        "format": "UCOPE_SCOUT_R01_COMPLETE_RESULT_V1", "schema_version": 1,
        "object_id": config.object_id, "complete": True, "config": config.to_dict(),
        "run_binding": run_binding, "checkpoints": records,
        "internal_result": {"evaluations": evaluations, "gates": {}, "support_histograms": {}, "support_limited": {}},
    }
    ledger = {"config": config.to_dict(), "run_binding": run_binding}
    terminal = {
        "config": config.to_dict(), "run_binding": run_binding,
        "checkpoint_inventory_aggregate_sha256": hashlib.sha256(_canonical(records)).hexdigest(),
    }
    for name, value in (("result.json", result), ("resource-ledger.json", ledger), ("terminal-receipt.json", terminal)):
        (complete / name).write_bytes(_canonical(value))
    binding = AuditBinding(
        result_sha256=_sha(complete / "result.json"),
        resource_ledger_sha256=_sha(complete / "resource-ledger.json"),
        terminal_receipt_sha256=_sha(complete / "terminal-receipt.json"),
        checkpoint_inventory_sha256=hashlib.sha256(_canonical(records)).hexdigest(),
        source_aggregate="2" * 64, manifest_digest="1" * 64, assessment_digest="3" * 64,
    )
    return complete, binding


def test_complete_tree_binds_72_inventory_and_two_independent_readonly_passes(tmp_path):
    complete, binding = _synthetic_complete(tmp_path)
    before = snapshot_input_tree(complete, binding)
    audit = audit_complete_tree(complete, binding)
    after = snapshot_input_tree(complete, binding)
    assert before["checkpoint_inventory"] == after["checkpoint_inventory"]
    assert len(audit["odd_rows"]) == 72 and len(audit["even_rows"]) == 72
    assert audit["read_counts"] == {"odd": 72, "even": 72}
    assert all(row["match"] for row in audit["even_match"])
    assert all("acquisition_evaluations" not in row["retained"] for row in audit["even_rows"])
    assert audit["input_inventory_before"] == audit["input_inventory_after"]


def test_checkpoint_rng_and_activity_literals_are_verified_without_builders(tmp_path):
    torch = pytest.importorskip("torch")
    complete, binding = _synthetic_complete(tmp_path)
    snapshot = snapshot_input_tree(complete, binding)
    config = ScoutConfig.from_dict(snapshot["config"])
    record = dict(snapshot["checkpoint_inventory"][0])
    path = complete / record["locator"]
    original = path.read_bytes()

    payload = torch.load(path, map_location="cpu", weights_only=False)
    payload["rng"] = {**payload["rng"], "counter_addressed": False}
    torch.save(payload, path)
    rng_record = {**record, "size_bytes": path.stat().st_size, "sha256": _sha(path)}
    with pytest.raises(ValueError, match="RNG"):
        _load_policy_checkpoint(
            path, rng_record, complete_root=complete, config=config,
            run_binding=snapshot["run_binding"],
        )

    path.write_bytes(original)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    payload["activity"]["root_optimizer_updates"] += 1
    torch.save(payload, path)
    activity_record = {**record, "size_bytes": path.stat().st_size, "sha256": _sha(path)}
    with pytest.raises(ValueError, match="activity/progress"):
        _load_policy_checkpoint(
            path, activity_record, complete_root=complete, config=config,
            run_binding=snapshot["run_binding"],
        )


def test_complete_tree_rejects_tamper_missing_duplicate_extra_and_even_mismatch(tmp_path):
    complete, binding = _synthetic_complete(tmp_path)
    extra_directory = complete / "empty-extra-directory"
    extra_directory.mkdir()
    with pytest.raises(ValueError, match="directory inventory"):
        snapshot_input_tree(complete, binding)
    extra_directory.rmdir()

    dangling = complete / "dangling-checkpoint-link.pt"
    try:
        dangling.symlink_to(complete / "missing-target.pt")
    except OSError:
        pass
    else:
        with pytest.raises(ValueError, match="symlink"):
            snapshot_input_tree(complete, binding)
        dangling.unlink()

    extra = complete / "checkpoints" / "extra.pt"
    extra.write_bytes(b"extra")
    with pytest.raises(ValueError, match="file inventory"):
        snapshot_input_tree(complete, binding)
    extra.unlink()

    result_path = complete / "result.json"
    result = json.loads(result_path.read_text())
    result["checkpoints"].append(dict(result["checkpoints"][0]))
    result_path.write_bytes(_canonical(result))
    duplicate_binding = AuditBinding(
        result_sha256=_sha(result_path), resource_ledger_sha256=binding.resource_ledger_sha256,
        terminal_receipt_sha256=binding.terminal_receipt_sha256,
        checkpoint_inventory_sha256=hashlib.sha256(_canonical(result["checkpoints"])).hexdigest(),
        source_aggregate=binding.source_aggregate, manifest_digest=binding.manifest_digest,
        assessment_digest=binding.assessment_digest,
    )
    with pytest.raises(ValueError, match="identity|72"):
        snapshot_input_tree(complete, duplicate_binding)

    complete2, binding2 = _synthetic_complete(tmp_path / "second")
    result2 = json.loads((complete2 / "result.json").read_text())
    result2["internal_result"]["evaluations"][0]["all_unique"] = not result2["internal_result"]["evaluations"][0]["all_unique"]
    (complete2 / "result.json").write_bytes(_canonical(result2))
    mismatch_binding = AuditBinding(
        result_sha256=_sha(complete2 / "result.json"), resource_ledger_sha256=binding2.resource_ledger_sha256,
        terminal_receipt_sha256=binding2.terminal_receipt_sha256,
        checkpoint_inventory_sha256=binding2.checkpoint_inventory_sha256,
        source_aggregate=binding2.source_aggregate, manifest_digest=binding2.manifest_digest,
        assessment_digest=binding2.assessment_digest,
    )
    with pytest.raises(ValueError, match="even rescore mismatch"):
        audit_complete_tree(complete2, mismatch_binding)


def test_single_handle_reader_rejects_same_bytes_path_swap_between_lstat_and_open(tmp_path, monkeypatch):
    complete, binding = _synthetic_complete(tmp_path / "scientific")
    target = complete / "result.json"
    replacement = tmp_path / "replacement-result.json"
    replacement.write_bytes(target.read_bytes())
    real_open = audit_module.os.open
    swapped = False

    def swapping_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if Path(path) == target.absolute() and not swapped:
            swapped = True
            audit_module.os.replace(replacement, target)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(audit_module.os, "open", swapping_open)
    with pytest.raises(ValueError, match="identity changed before open"):
        snapshot_input_tree(complete, binding)
    assert swapped is True


def test_execute_route_publishes_one_create_once_zero_effect_resource_bound_json(tmp_path):
    complete, binding = _synthetic_complete(tmp_path / "scientific")
    receipt = _fresh_admission(tmp_path)
    output = tmp_path / "audit.json"
    execute_audit_to_output(complete, receipt, output, binding=binding)
    value = json.loads(output.read_text(encoding="utf-8"))
    assert value["effect_counters"] == EFFECT_COUNTERS and set(value["effect_counters"].values()) == {0}
    assert value["admission"]["unchanged"] is True
    assert value["admission"]["receipt_sha256_before"] == value["admission"]["receipt_sha256_after"]
    assert value["resources"]["cap_pass"] is True
    assert value["resources"]["pre_tail_observed"]["device"] == "cpu"
    assert value["resources"]["pre_tail_observed"]["peak_process_count"] == 1
    assert value["publication"]["output_size_bytes"] == output.stat().st_size
    assert value["resources"]["durable_peak_bytes"] == output.stat().st_size
    assert value["resources"]["prospective_tail_envelope"]["wall_seconds"] == 60.0
    assert value["implementation_sources_before"] == value["implementation_sources_after"]
    assert validate_audit_artifact(value, expected_size_bytes=output.stat().st_size, binding=binding) == value
    route_tampered = json.loads(json.dumps(value))
    route_tampered["route"]["route"] = "INVALID_ROUTE"
    with pytest.raises(ValueError, match="route"):
        validate_audit_artifact(route_tampered, expected_size_bytes=output.stat().st_size, binding=binding)
    summary_tampered = json.loads(json.dumps(value))
    summary_tampered["summaries"]["policy_categories"][0]["competent"] = not summary_tampered["summaries"]["policy_categories"][0]["competent"]
    with pytest.raises(ValueError, match="summar"):
        validate_audit_artifact(summary_tampered, expected_size_bytes=output.stat().st_size, binding=binding)
    direct_tampered = json.loads(json.dumps(value))
    direct_tampered["odd_rows"][0]["root_hamming"] = 999
    with pytest.raises(ValueError, match="direct score|odd policy|summar"):
        validate_audit_artifact(direct_tampered, expected_size_bytes=output.stat().st_size, binding=binding)

    forged_input = json.loads(json.dumps(value))
    forged_input["input_inventory_before"]["top_hashes"]["result.json"] = "0" * 64
    forged_input["input_inventory_after"]["top_hashes"]["result.json"] = "0" * 64
    with pytest.raises(ValueError, match="input.*binding|top.*digest"):
        validate_audit_artifact(forged_input, expected_size_bytes=output.stat().st_size, binding=binding)

    forged_checkpoint = json.loads(json.dumps(value))
    forged_checkpoint["odd_rows"][0]["checkpoint"]["locator"] = "wrong.pt"
    with pytest.raises(ValueError, match="checkpoint.*join"):
        validate_audit_artifact(forged_checkpoint, expected_size_bytes=output.stat().st_size, binding=binding)

    leaked_even = json.loads(json.dumps(value))
    leaked_even["even_rows"][0]["retained"]["acquisition_evaluations"] = 999
    with pytest.raises(ValueError, match="retained.*field|even.*inventory"):
        validate_audit_artifact(leaked_even, expected_size_bytes=output.stat().st_size, binding=binding)

    invalid_admission = json.loads(json.dumps(value))
    embedded = invalid_admission["admission"]["receipt"]
    embedded["available_physical_bytes"] = 1
    raw_receipt = {
        key: item for key, item in embedded.items()
        if key not in {"receipt_sha256", "provenance"}
    }
    forged_digest = hashlib.sha256(
        (json.dumps(raw_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    ).hexdigest()
    embedded["receipt_sha256"] = forged_digest
    invalid_admission["admission"]["receipt_sha256_before"] = forged_digest
    invalid_admission["admission"]["receipt_sha256_after"] = forged_digest
    invalid_admission["admission"]["receipt_sha256_prepublication"] = forged_digest
    with pytest.raises(ValueError, match="4 GiB|admission"):
        validate_audit_artifact(invalid_admission, expected_size_bytes=output.stat().st_size, binding=binding)

    invalid_timestamps = json.loads(json.dumps(value))
    embedded = invalid_timestamps["admission"]["receipt"]
    embedded["captured_at"] = "x" * len(embedded["captured_at"])
    embedded["assessed_at"] = "y" * len(embedded["assessed_at"])
    raw_receipt = {
        key: item for key, item in embedded.items()
        if key not in {"receipt_sha256", "provenance"}
    }
    forged_digest = hashlib.sha256(
        (json.dumps(raw_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    ).hexdigest()
    embedded["receipt_sha256"] = forged_digest
    invalid_timestamps["admission"]["receipt_sha256_before"] = forged_digest
    invalid_timestamps["admission"]["receipt_sha256_after"] = forged_digest
    invalid_timestamps["admission"]["receipt_sha256_prepublication"] = forged_digest
    with pytest.raises(ValueError, match="timestamp|interval|ISO"):
        validate_audit_artifact(invalid_timestamps, expected_size_bytes=output.stat().st_size, binding=binding)

    negative_rss = json.loads(json.dumps(value))
    negative_rss["resources"]["pre_tail_observed"]["peak_rss_bytes"] = -1
    negative_rss["resources"]["prospective_total_bound"]["peak_rss_bytes"] = 128 * 1024**2 - 1
    with pytest.raises(ValueError, match="resource|RSS|rss"):
        validate_audit_artifact(negative_rss, expected_size_bytes=output.stat().st_size, binding=binding)
    assert not list(tmp_path.glob(".ucope-odd-support-audit-scratch-*"))
    with pytest.raises(FileExistsError, match="create-once"):
        execute_audit_to_output(complete, receipt, output, binding=binding)


def test_strict_core_and_implementation_source_validators_refuse_incomplete_or_tampered_evidence():
    with pytest.raises(ValueError, match="core field inventory"):
        validate_audit_core({"format": "synthetic-incomplete"})
    source = snapshot_implementation_sources()
    assert validate_implementation_source_snapshots(source, source) == source
    tampered = json.loads(json.dumps(source))
    tampered["files"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="changed"):
        validate_implementation_source_snapshots(source, tampered)
    forged = json.loads(json.dumps(source))
    forged["files"][0]["locator"] = "experiments/candidates/ucope/competence_first_scout_r01/forged.py"
    forged["aggregate_sha256"] = hashlib.sha256(_canonical(forged["files"])).hexdigest()
    with pytest.raises(ValueError, match="locator"):
        validate_implementation_source_snapshots(forged, forged)


def test_monitor_cap_or_readback_failure_never_leaves_scientific_output(tmp_path, monkeypatch):
    complete, binding = _synthetic_complete(tmp_path / "scientific")
    receipt = _fresh_admission(tmp_path)
    valid_core = audit_complete_tree(complete, binding)
    monkeypatch.setattr(audit_module, "audit_complete_tree", lambda *args, **kwargs: valid_core)

    class BrokenMonitor(AuditResourceMonitor):
        def finish(self):
            raise ValueError("monitor failed")

    with monkeypatch.context() as scoped:
        scoped.setattr(audit_module, "AuditResourceMonitor", BrokenMonitor)
        output = tmp_path / "monitor-failure.json"
        with pytest.raises(ValueError, match="monitor failed"):
            execute_audit_to_output(complete, receipt, output, binding=binding)
        assert not output.exists()

    class TailOverrunMonitor(AuditResourceMonitor):
        def finish(self):
            value = super().finish()
            return {**value, "wall_seconds": value["wall_seconds"] + 61.0}

    with monkeypatch.context() as scoped:
        scoped.setattr(audit_module, "AuditResourceMonitor", TailOverrunMonitor)
        output = tmp_path / "tail-overrun.json"
        with pytest.raises(ValueError, match="tail exceeded frozen envelope: wall_seconds"):
            execute_audit_to_output(complete, receipt, output, binding=binding)
        assert not output.exists()

    with monkeypatch.context() as scoped:
        scoped.setattr(
            audit_module, "_validate_resources",
            lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("cap failed")),
        )
        output = tmp_path / "cap-failure.json"
        with pytest.raises(ValueError, match="cap failed"):
            execute_audit_to_output(complete, receipt, output, binding=binding)
        assert not output.exists()

    with monkeypatch.context() as scoped:
        original_reader = audit_module._read_plain_file_once
        scoped.setattr(
            audit_module,
            "_read_plain_file_once",
            lambda path, root: (
                b"bad" if Path(path).name == "artifact.json" else original_reader(Path(path), Path(root))
            ),
        )
        output = tmp_path / "readback-failure.json"
        with pytest.raises(ValueError, match="readback"):
            execute_audit_to_output(complete, receipt, output, binding=binding)
        assert not output.exists()


def test_cli_has_only_frozen_three_argument_route_and_hardcodes_binding(tmp_path, monkeypatch):
    observed = []
    monkeypatch.setattr(
        audit_cli, "execute_audit_to_output",
        lambda complete, admission, output, *, binding: observed.append(
            (complete, admission, output, binding)
        ),
    )
    assert audit_cli.main([
        "--complete-root", "complete", "--admission-receipt", "admit.json",
        "--output", "audit.json",
    ]) == 0
    assert observed == [("complete", "admit.json", "audit.json", ACCEPTED_BINDING)]
    with pytest.raises(SystemExit):
        audit_cli.main([
            "--complete-root", "complete", "--admission-receipt", "admit.json",
            "--output", "audit.json", "--binding", "override",
        ])
    source = audit_cli.__file__ and Path(audit_cli.__file__).read_text(encoding="utf-8")
    assert "run_workload" not in source and "Optimizer" not in source and "torch" not in source
