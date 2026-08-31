import ast
import importlib
import json
import sys
from pathlib import Path

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.analysis import (
    dependency_firewall_observation,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    NATIVE_REGISTRY_KEY,
    SCHEMA_FILES,
    load_schema,
)


PACKAGE = Path(
    "experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01"
)


def test_isolated_source_import_graph_has_no_historical_apfi_network_gpu_or_training_edge():
    observed = dependency_firewall_observation()
    assert observed["passed"] is True
    assert observed["historical_risp_or_apfi_imports"] == []
    assert observed["network_imports"] == []
    assert observed["gpu_or_training_imports"] == []
    assert observed["historical_coordinates_read"] is False
    assert observed["historical_results_read"] is False
    assert observed["apfi_artifacts_read"] is False


def test_package_and_pre_result_cli_imports_are_action_inert():
    prefixes = (
        "experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.controllers",
        "experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reference_host",
    )
    for name in prefixes:
        sys.modules.pop(name, None)
    package = importlib.import_module(
        "experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01"
    )
    importlib.import_module(
        "experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.cli"
    )
    assert package.SPEC_SCHEMA == "RISP-ECR-R01-SPEC-V1"
    assert all(name not in sys.modules for name in prefixes)


def test_schemas_are_local_and_have_no_external_document_refs():
    for schema_name in SCHEMA_FILES:
        schema = load_schema(schema_name)
        assert schema["$id"] == schema_name
        for node in ast.walk(ast.parse(repr(schema))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith("http"):
                    assert node.value == "https://json-schema.org/draft/2020-12/schema"
        encoded = json.dumps(schema)
        assert ".schema.json\"" not in encoded.replace(
            "https://json-schema.org/draft/2020-12/schema", ""
        )


def test_native_registry_key_is_fresh_and_not_a_historical_resume_key():
    assert NATIVE_REGISTRY_KEY == "RISP_ECR_R01_EXACT_EVENT_HOST_V1"
    folded = NATIVE_REGISTRY_KEY.casefold()
    assert "g_init" not in folded
    assert "b1" not in folded and "b2" not in folded and "b3" not in folded
    assert "resume" not in folded


def test_no_hash_based_admission_identity_or_artifact_gate_exists():
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(PACKAGE.rglob("*"))
        if path.suffix in {".py", ".cpp", ".json"}
    ).casefold()
    for forbidden in ("hashlib", "sha256", "schema_hash", "view_digest", "source_digest"):
        assert forbidden not in sources
    native = (PACKAGE / "native_backend.py").read_text(encoding="utf-8")
    assert "_PROCESS_BUILD_TOKEN" in native
    assert "SOURCE.read_bytes" not in native
