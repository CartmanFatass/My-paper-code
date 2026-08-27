from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import empirical_transaction
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_contract import (
    DEFAULT_RUN_BINDING,
    DIRECTION_GIT_PATHS,
    OUTPUT_ROOT,
    PANELS,
    LEARNED_ARMS,
    NONLEARNED_CONTROLS,
    PAYLOAD_MODULE,
    REGISTERED_SEEDS,
    REQUIRED_DIAGNOSTICS,
    RNG_NAMESPACES,
    RUN_ID,
    REPLACEMENT_RUN_BINDING,
    RunBinding,
    TERMINAL_RESULT_MAP,
    checkpoint_slots,
    conservative_estimate_document,
    document_sha256,
    parameters_document,
    payload_argv,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_engine import (
    ProductionExecutionRefusal,
    RuntimePaths,
    _require_launch,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_manifest import (
    ManifestError,
    build_checkpoint_manifest_contract,
    build_prelaunch_manifest,
    build_source_manifest,
    complete_checkpoint_manifest,
    emit_prelaunch_artifacts,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_validation import (
    PrelaunchRefusal,
    reject_forbidden_options,
    read_canonical_json,
    validate_checkpoint_manifest_contract,
    validate_exact_documents,
    validate_output_precondition,
    validate_prelaunch_manifest,
    validate_source_manifest,
)


ROOT = Path(__file__).resolve().parents[4]


def test_exact_complete_transaction_contract_is_result_independent() -> None:
    parameters = parameters_document()
    assert REGISTERED_SEEDS == (101, 211, 307, 401, 503, 601, 701, 809, 907, 1009)
    assert PANELS == ("PERSISTENT", "REDRAW", "SEVERED")
    assert LEARNED_ARMS == ("COUNT", "RAW", "BELIEF_FEATURE")
    assert NONLEARNED_CONTROLS == (
        "BELIEF_DP", "IMMEDIATE_DP", "FORCED_PROBE_BLIND_DP", "RAW_PERMAVG"
    )
    assert RNG_NAMESPACES == ("REGIME", "PROBE_ACTUAL", "PROBE_DISPLAY", "TAIL_Z", "ACTION", "INIT")
    assert parameters["training"] == {
        "batches": 320,
        "episodes_per_arm_batch": 256,
        "joint_adamw_steps_per_batch": 1,
        "final_checkpoint_batch_only": 320,
        "worker_count": 1,
        "dtype": "FP32",
    }
    assert parameters["checkpoint_slot_count"] == len(checkpoint_slots()) == 90
    assert parameters["evaluation"]["required_diagnostics"] == list(REQUIRED_DIAGNOSTICS)
    assert parameters["evaluation"]["terminal_result_map"] == list(TERMINAL_RESULT_MAP)
    assert len(TERMINAL_RESULT_MAP) == 6
    assert parameters["rerun_permitted"] is False
    assert parameters["result_responsive_options"] == []


def test_payload_uses_only_renamed_runner_and_has_no_override_surface() -> None:
    argv = payload_argv()
    assert argv[1:3] == ("-m", PAYLOAD_MODULE)
    assert "production" not in argv[2].split(".")[-1]
    assert not (ROOT / "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production.py").exists()
    assert (ROOT / "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/empirical_transaction.py").is_file()
    forbidden = {"--seed", "--master-seed", "--arm", "--panel", "--diagnostic", "--partial", "--result", "--query", "--rerun"}
    assert forbidden.isdisjoint(argv)
    for option in forbidden:
        with pytest.raises(PrelaunchRefusal, match="override"):
            reject_forbidden_options((option, "technical-fixture"))


def test_source_checkpoint_and_prelaunch_manifests_are_hash_bound() -> None:
    source = build_source_manifest(ROOT)
    checkpoints = build_checkpoint_manifest_contract()
    prelaunch = build_prelaunch_manifest(
        source_manifest=source, code_sha=None, branch="main", empirical_activity_released=False
    )
    validate_source_manifest(ROOT, source)
    validate_checkpoint_manifest_contract(checkpoints)
    validate_prelaunch_manifest(prelaunch, source_manifest=source, release_required=False)
    assert prelaunch["run_id"] == RUN_ID
    assert prelaunch["output_effect"] == {
        "kind": "DIRECTORY_CREATE_ONLY",
        "resource_id": OUTPUT_ROOT,
        "operation": "create_and_populate_once",
    }
    assert prelaunch["publication"] == "ONE_ATOMIC_COMPLETE_PACKAGE_ONLY"
    assert prelaunch["git"]["required_branch_prefix"] == "omp/ucope/"
    assert prelaunch["git"]["direction_owned_paths"] == list(DIRECTION_GIT_PATHS)
    assert prelaunch["empirical_activity_released"] is False
    assert prelaunch["operator_now"] is False
    assert prelaunch["effect_refs"] == []

    mutated = copy.deepcopy(source)
    mutated["files"][0]["sha256"] = "0" * 64
    with pytest.raises(PrelaunchRefusal, match="source hash"):
        validate_source_manifest(ROOT, mutated)
    broken = copy.deepcopy(checkpoints)
    del broken["slots"][0]["sha256_required"]
    with pytest.raises(PrelaunchRefusal, match="checkpoint"):
        validate_checkpoint_manifest_contract(broken)


def test_future_inventory_requires_all_90_ordered_content_hashes() -> None:
    rows = [
        {**slot, "sha256": f"{index + 1:064x}", "model_sha256": f"{index + 101:064x}"}
        for index, slot in enumerate(checkpoint_slots())
    ]
    complete = complete_checkpoint_manifest(rows)
    assert complete["complete"] is True
    assert complete["slot_count"] == len(complete["slots"]) == 90
    with pytest.raises(ManifestError, match="90"):
        complete_checkpoint_manifest(rows[:-1])
    del rows[0]["sha256"]
    with pytest.raises(ManifestError, match="hashes"):
        complete_checkpoint_manifest(rows)


def test_nonregistered_fixtures_prove_refusals_without_activity(tmp_path: Path) -> None:
    parameters = parameters_document()
    estimate = conservative_estimate_document()
    validate_exact_documents(parameters, estimate)
    altered = copy.deepcopy(parameters)
    altered["registered_master_seeds"] = [0xC300000000000000]
    with pytest.raises(PrelaunchRefusal, match="parameter override"):
        validate_exact_documents(altered, estimate)

    assert validate_output_precondition(tmp_path) == "ABSENT"
    reserved = tmp_path / Path(*OUTPUT_ROOT.split("/"))
    reserved.mkdir(parents=True)
    assert validate_output_precondition(tmp_path) == "EMPTY"
    (reserved / "technical-only.txt").write_text("not a result", encoding="utf-8")
    with pytest.raises(PrelaunchRefusal, match="nonempty"):
        validate_output_precondition(tmp_path)

    source = build_source_manifest(ROOT)
    unreleased = build_prelaunch_manifest(
        source_manifest=source, code_sha=None, branch="main", empirical_activity_released=False
    )
    with pytest.raises(PrelaunchRefusal, match="hash is missing|release is absent"):
        validate_prelaunch_manifest(unreleased, source_manifest=source, release_required=True)


def test_cli_surface_is_complete_only_and_requires_later_manifests(tmp_path: Path) -> None:
    actions = empirical_transaction.parser()._actions
    options = {option for action in actions for option in action.option_strings}
    assert options == {
        "-h", "--help", "--run-id", "--output-root", "--hmasd-manifest",
    }
    with pytest.raises(SystemExit):
        empirical_transaction.validate_launch((), repository_root=ROOT)
    with pytest.raises(PrelaunchRefusal, match="override"):
        empirical_transaction.validate_launch(("--seed", "123"), repository_root=ROOT)
    assert RUN_ID not in json.dumps({"fixture_seed": 0xC300000000000000})


def test_five_prelaunch_artifacts_are_atomic_single_canonical_json_values(tmp_path: Path) -> None:
    refs = emit_prelaunch_artifacts(
        ROOT, tmp_path, observed_branch="main", code_sha=None
    )
    assert tuple(refs) == (
        "S3_PARAMETERS.json",
        "S3_CONSERVATIVE_ESTIMATE.json",
        "S3_SOURCE_MANIFEST.json",
        "S3_CHECKPOINT_MANIFEST_CONTRACT.json",
        "S3_PRELAUNCH_MANIFEST.json",
    )
    parsed = {name: read_canonical_json(tmp_path / name) for name in refs}
    assert parsed["S3_PARAMETERS.json"] == parameters_document()
    assert parsed["S3_CONSERVATIVE_ESTIMATE.json"] == conservative_estimate_document()
    assert parsed["S3_CHECKPOINT_MANIFEST_CONTRACT.json"] == build_checkpoint_manifest_contract()
    prelaunch = parsed["S3_PRELAUNCH_MANIFEST.json"]
    assert prelaunch["parameters_sha256"] == document_sha256(parsed["S3_PARAMETERS.json"])
    assert prelaunch["estimate_sha256"] == document_sha256(parsed["S3_CONSERVATIVE_ESTIMATE.json"])
    assert prelaunch["source_manifest_sha256"] == document_sha256(parsed["S3_SOURCE_MANIFEST.json"])
    assert prelaunch["checkpoint_manifest_sha256"] == document_sha256(
        parsed["S3_CHECKPOINT_MANIFEST_CONTRACT.json"]
    )

    target = tmp_path / "S3_PARAMETERS.json"
    target.write_bytes(target.read_bytes() + b"\\n")
    with pytest.raises(PrelaunchRefusal, match="canonical"):
        read_canonical_json(target)


def test_default_binding_preserves_exact_legacy_contract_bytes() -> None:
    assert parameters_document() == parameters_document(DEFAULT_RUN_BINDING)
    assert conservative_estimate_document() == conservative_estimate_document(
        DEFAULT_RUN_BINDING
    )
    assert payload_argv() == payload_argv(DEFAULT_RUN_BINDING)
    assert document_sha256(parameters_document()) == (
        "53dec90df4c1ecb66701e18b42283f455fda01a874dec0ebc20c2d556afddea3"
    )
    assert document_sha256(conservative_estimate_document()) == (
        "21610e3f71e992e01341eba7ee21001702e65eea68196ef7c345c2b6edb9676d"
    )
    assert document_sha256(build_checkpoint_manifest_contract()) == (
        "cb1d6621afdbb4456d8b6fca4a9eb65d8e1a86390c1d8de67ad64a2d9a4f41f2"
    )
    source = build_source_manifest(ROOT)
    implicit = build_prelaunch_manifest(
        source_manifest=source, code_sha=None, branch="main"
    )
    explicit = build_prelaunch_manifest(
        source_manifest=source,
        code_sha=None,
        branch="main",
        binding=DEFAULT_RUN_BINDING,
    )
    assert implicit == explicit
    assert "authority_refs" not in implicit
    assert "run_binding" not in source


def test_replacement_binding_reaches_all_nonregistered_prelaunch_layers(
    tmp_path: Path,
) -> None:
    binding = REPLACEMENT_RUN_BINDING
    source = build_source_manifest(ROOT, binding=binding)
    parameters = parameters_document(binding)
    estimate = conservative_estimate_document(binding)
    prelaunch = build_prelaunch_manifest(
        source_manifest=source,
        code_sha=None,
        branch="main",
        empirical_activity_released=False,
        binding=binding,
    )

    validate_exact_documents(parameters, estimate, binding=binding)
    validate_source_manifest(ROOT, source, binding=binding)
    validate_checkpoint_manifest_contract(
        build_checkpoint_manifest_contract(binding), binding=binding
    )
    validate_prelaunch_manifest(
        prelaunch,
        source_manifest=source,
        release_required=False,
        binding=binding,
    )
    assert parameters["run_id"] == binding.run_id
    assert estimate["run_id"] == binding.run_id
    assert prelaunch["output_effect"] == binding.output_effect()
    assert prelaunch["authority_refs"] == binding.authority_document()
    assert prelaunch["effect_refs"] == []
    assert prelaunch["empirical_activity_released"] is False
    assert prelaunch["operator_now"] is False
    refs = emit_prelaunch_artifacts(
        ROOT,
        tmp_path,
        observed_branch="main",
        code_sha=None,
        binding=binding,
    )
    emitted = read_canonical_json(tmp_path / "S3_PRELAUNCH_MANIFEST.json")
    assert len(refs) == 5
    validate_prelaunch_manifest(
        emitted,
        source_manifest=read_canonical_json(tmp_path / "S3_SOURCE_MANIFEST.json"),
        release_required=False,
        binding=binding,
    )


def test_cross_bound_identity_source_effect_and_authority_are_refused() -> None:
    binding = REPLACEMENT_RUN_BINDING
    source = build_source_manifest(ROOT, binding=binding)
    prelaunch = build_prelaunch_manifest(
        source_manifest=source, code_sha=None, branch="main", binding=binding
    )

    with pytest.raises(PrelaunchRefusal, match="run-id"):
        validate_prelaunch_manifest(
            prelaunch,
            source_manifest=source,
            release_required=False,
            binding=DEFAULT_RUN_BINDING,
        )
    default_source = build_source_manifest(ROOT)
    with pytest.raises(ManifestError, match="source manifest"):
        build_prelaunch_manifest(
            source_manifest=default_source,
            code_sha=None,
            branch="main",
            binding=binding,
        )
    with pytest.raises(PrelaunchRefusal, match="source"):
        validate_prelaunch_manifest(
            prelaunch,
            source_manifest=default_source,
            release_required=False,
            binding=binding,
        )
    wrong_effect = copy.deepcopy(prelaunch)
    wrong_effect["output_effect"]["resource_id"] = OUTPUT_ROOT
    with pytest.raises(PrelaunchRefusal, match="firewall"):
        validate_prelaunch_manifest(
            wrong_effect,
            source_manifest=source,
            release_required=False,
            binding=binding,
        )
    wrong_authority = copy.deepcopy(prelaunch)
    wrong_authority["authority_refs"][0]["sha256"] = "0" * 64
    with pytest.raises(PrelaunchRefusal, match="authority"):
        validate_prelaunch_manifest(
            wrong_authority,
            source_manifest=source,
            release_required=False,
            binding=binding,
        )
    noncanonical = RunBinding(binding.run_id, binding.output_root, ())
    with pytest.raises(ValueError, match="canonical"):
        parameters_document(noncanonical)


def test_payload_and_engine_consume_the_same_explicit_replacement_binding(
    tmp_path: Path,
) -> None:
    binding = REPLACEMENT_RUN_BINDING
    assert empirical_transaction.resolve_run_binding(payload_argv(binding)[3:]) is binding
    precondition_root = tmp_path / "precondition"
    assert validate_output_precondition(precondition_root, binding=binding) == "ABSENT"
    with pytest.raises(PrelaunchRefusal, match="output-root"):
        validate_output_precondition(
            precondition_root, OUTPUT_ROOT, binding=binding
        )
    output = tmp_path / Path(*binding.output_root.split("/"))
    for name in ("checkpoints", "artifacts", "metrics"):
        (output / name).mkdir(parents=True, exist_ok=True)
    code_sha = "1" * 40
    hmasd = {
        "run_id": binding.run_id,
        "direction_id": "ucope",
        "code_sha": code_sha,
        "cwd": str(tmp_path.resolve()),
        "command": list(payload_argv(binding)),
        "status": "RUNNING",
        "parameters": parameters_document(binding),
        "estimate": {
            key: conservative_estimate_document(binding)[key]
            for key in ("wall_seconds", "basis", "peak_memory_gib")
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(hmasd), encoding="utf-8")
    argv = (
        "--run-id",
        binding.run_id,
        "--output-root",
        binding.output_root,
        "--hmasd-manifest",
        str(manifest_path),
    )
    launch = empirical_transaction.validate_launch(
        argv, repository_root=tmp_path, binding=binding
    )
    paths = RuntimePaths.from_repository(tmp_path, binding)
    assert paths.binding is binding
    assert paths.output_root == output.resolve()
    assert _require_launch(launch, paths, binding) == (binding.run_id, code_sha)

    with pytest.raises(PrelaunchRefusal, match="override"):
        empirical_transaction.validate_launch(
            argv, repository_root=tmp_path, binding=DEFAULT_RUN_BINDING
        )
    with pytest.raises(ProductionExecutionRefusal, match="immutable"):
        _require_launch(launch, paths, DEFAULT_RUN_BINDING)
