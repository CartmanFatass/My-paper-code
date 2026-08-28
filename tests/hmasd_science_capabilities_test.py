from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import hmasd_science_capabilities as capabilities

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 project env
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_science_capabilities.py"
CATALOG = ROOT / "configs" / "scientific-capabilities-v1.toml"
SOURCES = ROOT / "configs" / "scientific-capability-sources-v1.json"
CRITICAL_SKILL = (
    ROOT / ".agents" / "skills" / "hmasd-scientific-critical-thinking" / "SKILL.md"
)
INSTRUMENT_LEAF_ROLES = {
    "hmasd-research-scout",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
    "hmasd-research-innovator",
    "hmasd-implementer",
    "hmasd-implementer-terra",
    "hmasd-verifier",
}
DIRECTION_AUTHORITY = (
    ROOT / "docs" / "research" / "candidates" / "field_slot_coordination" / "DIRECTION.md"
)
GOLDEN_RAW_OBSERVATION = (
    ROOT
    / "tests/fixtures/hmasd_science/critical_thinking_field_slot/temp/directions"
    / "field_slot_coordination/test/instruments/critical-thinking-field-slot-r01"
    / "observation.json"
)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_raw_observation(value: dict) -> Path:
    destination = ROOT / value["artifacts"][0]["path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == GOLDEN_RAW_OBSERVATION.read_bytes()
    else:
        shutil.copyfile(GOLDEN_RAW_OBSERVATION, destination)
    value["artifacts"][0]["sha256"] = sha256_path(destination)
    return destination


def instrument_candidate_path(value: dict, name: str = "sidecar-candidate.json") -> Path:
    return (ROOT / value["artifacts"][0]["path"]).parent / name


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def valid_evidence(direction_id: str = "field_slot_coordination") -> dict:
    evidence_id = "critical-thinking-field-slot-r01"
    return {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "direction_id": direction_id,
        "sidecar_path": (
            f"docs/research/candidates/{direction_id}/evidence/{evidence_id}.json"
        ),
        "owner_role": "EM",
        "producer_leaf": "hmasd-research-critic",
        "capability": {
            "capability_id": "scientific-critical-thinking",
            "skill_ref": {
                "path": ".agents/skills/hmasd-scientific-critical-thinking/SKILL.md",
                "sha256": sha256_path(CRITICAL_SKILL),
            },
            "tool": "reasoned-claim-audit",
            "tool_version": "1",
            "environment_ref": None,
            "effect_class": "local_read_only",
        },
        "frozen_operation": {
            "objective": "Bound the current field-slot coordination claim.",
            "input_refs": [
                {
                    "path": "docs/research/candidates/field_slot_coordination/DIRECTION.md",
                    "sha256": sha256_path(DIRECTION_AUTHORITY),
                }
            ],
            "judgment_criteria": [
                "Separate missing evidence from falsification.",
                "Name the strongest alternative explanation.",
            ],
            "constraints": {
                "claim_scope": "registered finite algorithm and UAV bridge"
            },
        },
        "invocation": {
            "kind": "manual",
            "argv": [],
            "cwd": ".",
            "entrypoint_ref": None,
        },
        "platform": {
            "os": "Windows",
            "architecture": "AMD64",
            "python": None,
        },
        "artifacts": [
            {
                "path": (
                    "temp/directions/field_slot_coordination/test/instruments/"
                    f"{evidence_id}/observation.json"
                ),
                "sha256": "3" * 64,
                "retention": "ephemeral",
            }
        ],
        "outcome": {
            "status": "OBSERVED",
            "core_observations": [
                "The authority explicitly records no finite registered algorithm object yet.",
                "Host law and objective, thresholds and comparator, and a UAV/runtime bridge are not bound.",
                "The frozen evidence cannot distinguish bootstrap incompleteness from underlying infeasibility.",
            ],
            "failure": None,
        },
        "assumptions": [],
        "limitations": ["This audit does not create direction authority."],
        "manager_interpretation": {
            "target_ref": {
                "path": "docs/research/candidates/field_slot_coordination/DIRECTION.md",
                "sha256": sha256_path(DIRECTION_AUTHORITY),
            },
            "impact_summary": "Retain the direction as preliminary.",
            "claim_ceiling": (
                "Do not infer an implemented algorithm, effective mechanism, causal "
                "benefit, comparative superiority, host-objective improvement, "
                "operational validity, UAV/runtime feasibility, or scientific readiness."
            ),
        },
    }


def test_list_filters_declared_capabilities_without_executing_them() -> None:
    result = run_cli(
        "list",
        "--role",
        "EM",
        "--question-type",
        "claim_critique",
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "capabilities": [
            {
                "capability_id": "scientific-critical-thinking",
                "effect_class": "local_read_only",
                "environment_id": "none",
                "skill_name": "hmasd-scientific-critical-thinking",
                "status": "active",
            }
        ],
        "schema_version": 1,
    }


def test_list_exposes_the_complete_v1_considered_capability_set() -> None:
    result = run_cli("list")

    assert result.returncode == 0, result.stderr
    statuses = {
        item["capability_id"]: item["status"]
        for item in json.loads(result.stdout)["capabilities"]
    }
    assert statuses == {
        "experimental-design": "candidate",
        "local-reference-implementation": "candidate",
        "networkx": "candidate",
        "numerical-verification": "candidate",
        "paper-lookup": "candidate",
        "profiling": "candidate",
        "pufferlib-marl": "candidate",
        "scientific-critical-thinking": "active",
        "scientific-visualization": "candidate",
        "stable-baselines3-reference": "candidate",
        "statistical-analysis": "candidate",
        "symbolic-math": "candidate",
        "torch-geometric-mechanism": "candidate",
        "uav-runtime-provenance": "candidate",
        "wolfram-symbolic-verification": "unavailable",
    }


def test_catalog_is_hash_bound_role_scoped_and_discovery_safe() -> None:
    catalog = tomllib.loads(CATALOG.read_text(encoding="utf-8"))
    source_lock = json.loads(SOURCES.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in source_lock["sources"]}
    rows = catalog["capabilities"]
    ids = [item["capability_id"] for item in rows]

    assert len(ids) == len(set(ids))
    assert len(sources) == len(source_lock["sources"])
    assert {
        item["source_id"] for item in source_lock["sources"]
        if item["eligibility"] == "excluded"
    } == {"literature-review", "research-lookup", "scientific-writing"}

    required_fields = {
        "capability_id",
        "status",
        "question_types",
        "owner_roles",
        "leaf_roles",
        "skill_name",
        "skill_path",
        "environment_id",
        "manifest_ref",
        "entrypoints",
        "effect_class",
        "invocation_kinds",
        "tool_name",
        "tool_version",
        "source_id",
        "source_sha256",
        "limitations",
        "unavailable_reason",
    }
    for item in rows:
        assert set(item) == required_fields
        assert item["status"] in {"candidate", "active", "unavailable"}
        assert item["question_types"] and len(item["question_types"]) == len(
            set(item["question_types"])
        )
        assert set(item["owner_roles"]) <= {"EM", "CM"}
        assert item["owner_roles"] and item["leaf_roles"]
        assert set(item["leaf_roles"]) <= INSTRUMENT_LEAF_ROLES
        assert item["source_id"] in sources
        assert item["source_sha256"] == sources[item["source_id"]]["computed_hash"]
        assert item["limitations"]
        if item["status"] == "active":
            expected = f".agents/skills/{item['skill_name']}/SKILL.md"
            assert item["skill_path"] == expected
            assert (ROOT / expected).is_file()
            if item["environment_id"] != "none":
                assert item["manifest_ref"]
                assert (ROOT / item["manifest_ref"]).is_file()
        else:
            assert item["skill_path"] == ""
            if item["skill_name"]:
                assert not (ROOT / ".agents" / "skills" / item["skill_name"]).exists()


def test_critical_thinking_skill_is_explicit_only_and_locally_valid() -> None:
    skill_root = ROOT / ".agents" / "skills" / "hmasd-scientific-critical-thinking"
    skill = skill_root / "SKILL.md"
    agent = skill_root / "agents" / "openai.yaml"
    text = skill.read_text(encoding="utf-8")
    policy = agent.read_text(encoding="utf-8")

    assert text.startswith("---\nname: hmasd-scientific-critical-thinking\n")
    assert "description: Use when an HMASD EM explicitly selects" in text
    assert "outcome: OBSERVED | FAILED | UNAVAILABLE" in text
    assert "Never output `PASS`" in text
    assert "allow_implicit_invocation: false" in policy


def test_representative_critical_thinking_evidence_and_raw_artifact_are_bound(
    tmp_path: Path,
) -> None:
    fixture = ROOT / "tests" / "fixtures" / "hmasd_science" / "critical_thinking_field_slot"
    sidecar = (
        fixture
        / "docs/research/candidates/field_slot_coordination/evidence"
        / "critical-thinking-field-slot-r01.json"
    )
    value = json.loads(sidecar.read_text(encoding="utf-8"))
    artifact = fixture / value["artifacts"][0]["path"]
    observation = json.loads(artifact.read_text(encoding="utf-8"))[
        "instrument_observation"
    ]
    runtime_artifact = materialize_raw_observation(value)

    candidate = instrument_candidate_path(value, f"pytest-{tmp_path.name}.json")
    candidate.write_bytes(sidecar.read_bytes())
    result = run_cli(
        "validate-evidence",
        "--path",
        str(candidate),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 0, result.stderr
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == value["artifacts"][0][
        "sha256"
    ]
    skill = ROOT / value["capability"]["skill_ref"]["path"]
    assert hashlib.sha256(skill.read_bytes()).hexdigest() == value["capability"][
        "skill_ref"
    ]["sha256"]
    assert observation["claim_classification"] == "supported"
    assert observation["core_observations"] == value["outcome"]["core_observations"]
    assert {threat["kind"] for threat in observation["threats"]} >= {
        "contrary_evidence",
        "missing_evidence",
        "scope_mismatch",
    }
    assert observation["strongest_alternative"]
    assert observation["decisive_missing_evidence"]
    assert "readiness" in observation["claim_ceiling"]
    assert "PASS" not in artifact.read_text(encoding="utf-8")
    candidate.unlink()


def test_doctor_observes_active_skill_without_installing_or_executing() -> None:
    result = run_cli("doctor", "--id", "scientific-critical-thinking")

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["available"] is True
    assert record["declared_status"] == "active"
    assert record["capability_id"] == "scientific-critical-thinking"
    assert record["observations"] == [
        "skill found: .agents/skills/hmasd-scientific-critical-thinking/SKILL.md",
        "environment: none",
        "entrypoints: none",
    ]
    assert "subprocess.run" not in SCRIPT.read_text(encoding="utf-8")


def test_catalog_loader_fails_closed_on_duplicate_capability_id(tmp_path: Path) -> None:
    value = CATALOG.read_text(encoding="utf-8")
    first = value.index("[[capabilities]]")
    second = value.index("[[capabilities]]", first + 1)
    duplicate = value[:second] + value[first:second] + value[second:]
    path = tmp_path / "duplicate.toml"
    path.write_text(duplicate, encoding="utf-8")

    with pytest.raises(capabilities.CapabilityError, match="duplicate capability_id"):
        capabilities._load_catalog(path)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("forbidden-leaf", "unknown leaf role"),
        ("generic-python", "dedicated repo entrypoint"),
        ("generic-shell", "dedicated repo entrypoint"),
        ("api-external", "dedicated repo entrypoint"),
    ],
)
def test_catalog_loader_rejects_forbidden_leaf_or_active_unsafe_entrypoint(
    tmp_path: Path, mutation: str, expected: str,
) -> None:
    value = CATALOG.read_text(encoding="utf-8")
    if mutation == "forbidden-leaf":
        value = value.replace(
            'leaf_roles = ["hmasd-research-critic", "hmasd-research-principles-analyst"]',
            'leaf_roles = ["Workflow-Clerk"]',
            1,
        )
    else:
        executable = {
            "generic-python": sys.executable.replace("\\", "/"),
            "generic-shell": "powershell.exe",
            "api-external": "provider.lookup",
        }[mutation]
        value = value.replace("entrypoints = []", f'entrypoints = ["{executable}"]', 1)
        value = value.replace(
            'invocation_kinds = ["manual"]',
            'invocation_kinds = ["api"]'
            if mutation == "api-external"
            else 'invocation_kinds = ["command"]',
            1,
        )
    path = tmp_path / "invalid.toml"
    path.write_text(value, encoding="utf-8")

    with pytest.raises(capabilities.CapabilityError, match=expected):
        capabilities._load_catalog(path)


def test_command_evidence_hash_binds_the_dedicated_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities, "ROOT", tmp_path)
    wrapper_relative = ".agents/skills/hmasd-probe/scripts/probe.py"
    wrapper = tmp_path / wrapper_relative
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("print('bounded probe')\n", encoding="utf-8")
    value = valid_evidence()
    value["capability"]["skill_ref"] = None
    value["invocation"] = {
        "kind": "command",
        "argv": [wrapper_relative, "--frozen"],
        "cwd": ".",
        "entrypoint_ref": {
            "path": wrapper_relative,
            "sha256": sha256_path(wrapper),
        },
    }
    catalog = {
        "capabilities": [
            {
                "capability_id": "scientific-critical-thinking",
                "status": "active",
                "owner_roles": ["EM"],
                "leaf_roles": ["hmasd-research-critic"],
                "effect_class": "local_read_only",
                "tool_name": "reasoned-claim-audit",
                "tool_version": "1",
                "invocation_kinds": ["command"],
                "entrypoints": [wrapper_relative],
                "skill_name": "hmasd-probe",
                "skill_path": "",
                "environment_id": "none",
            }
        ]
    }

    capabilities._validate_capability_binding(value, catalog)
    value["invocation"]["entrypoint_ref"]["sha256"] = "0" * 64

    with pytest.raises(capabilities.CapabilityError, match="entrypoint_ref sha256"):
        capabilities._validate_capability_binding(value, catalog)


def test_exact_root_resolution_rejects_an_in_repo_symlink_redirect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capabilities, "ROOT", tmp_path)
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    (redirected / "observation.json").write_text("{}", encoding="utf-8")
    exact_root = (
        tmp_path
        / "temp/directions/fixture/test/instruments/evidence-r01"
    )
    exact_root.parent.mkdir(parents=True)
    try:
        exact_root.symlink_to(redirected, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable on this host: {exc}")

    with pytest.raises(capabilities.CapabilityError, match="redirects the exact root"):
        capabilities._resolve_within_exact_root(
            "temp/directions/fixture/test/instruments/evidence-r01/observation.json",
            "temp/directions/fixture/test/instruments/evidence-r01",
            "instrument artifact",
            expect_file=True,
        )


def test_cli_exposes_no_execution_install_routing_or_state_mutation_commands() -> None:
    result = run_cli("--help")

    assert result.returncode == 0, result.stderr
    normalized = " ".join(result.stdout.lower().split())
    assert "{list,show,doctor,validate-evidence}" in normalized
    assert "--catalog" not in normalized
    for forbidden in (" run", " install", " execute", " route", " lifecycle", " mutate"):
        assert forbidden not in normalized


def test_show_reports_wolfram_as_unavailable_without_an_install_path() -> None:
    result = run_cli("show", "--id", "wolfram-symbolic-verification")

    assert result.returncode == 0, result.stderr
    capability = json.loads(result.stdout)["capability"]
    assert capability["capability_id"] == "wolfram-symbolic-verification"
    assert capability["status"] == "unavailable"
    assert capability["skill_path"] == ""
    assert capability["environment_id"] == "none"
    assert "not installed" in capability["unavailable_reason"].lower()


def test_doctor_observes_unavailable_wolfram_without_installing() -> None:
    result = run_cli("doctor", "--id", "wolfram-symbolic-verification")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "available": False,
        "capability_id": "wolfram-symbolic-verification",
        "declared_status": "unavailable",
        "observations": [
            "executable not found: wolframscript",
            "executable not found: math",
        ],
        "schema_version": 1,
    }


def test_validate_evidence_accepts_one_direction_owned_sidecar(tmp_path: Path) -> None:
    value = valid_evidence()
    materialize_raw_observation(value)
    path = instrument_candidate_path(value, f"pytest-{tmp_path.name}.json")
    path.write_text(json.dumps(value), encoding="utf-8")
    candidate_sha = sha256_path(path)

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "content_sha256": candidate_sha,
        "direction_id": "field_slot_coordination",
        "evidence_id": "critical-thinking-field-slot-r01",
        "schema_version": 1,
        "sidecar_path": value["sidecar_path"],
        "valid": True,
    }
    path.unlink()


@pytest.mark.parametrize(
    ("field", "captured"),
    [
        ("api_token", "sk-do-not-store"),
        ("OPENAI_API_KEY", "redacted-but-forbidden-field"),
        ("note", "Bearer abcdefghijklmnopqrstuvwxyz"),
        ("note", "AKIAABCDEFGHIJKLMNOP"),
    ],
)
def test_validate_evidence_rejects_secret_like_capture(
    tmp_path: Path, field: str, captured: str,
) -> None:
    value = valid_evidence()
    value["frozen_operation"]["constraints"][field] = captured
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "secret-like" in result.stderr


def test_validate_evidence_rejects_cross_direction_refs(tmp_path: Path) -> None:
    value = valid_evidence()
    value["frozen_operation"]["input_refs"][0]["path"] = (
        "docs/research/candidates/ucope/DIRECTION.md"
    )
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "cross-direction" in result.stderr


def test_validate_evidence_rejects_cross_direction_locator_hidden_in_constraints(
    tmp_path: Path,
) -> None:
    value = valid_evidence()
    value["frozen_operation"]["constraints"]["comparison_locator"] = (
        "docs/research/candidates/ucope/DIRECTION.md"
    )
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "cross-direction" in result.stderr


def test_validate_evidence_rejects_raw_artifact_outside_instrument_root(
    tmp_path: Path,
) -> None:
    value = valid_evidence()
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/unscoped-output.json"
    )
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "instrument artifact path" in result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("owner", "owner_role"),
        ("leaf", "producer_leaf"),
        ("candidate", "not active"),
        ("skill-hash", "skill_ref sha256"),
        ("effect", "effect_class"),
        ("tool", "tool does not match"),
        ("tool-version", "tool_version does not match"),
        ("invocation", "invocation kind"),
    ],
)
def test_validate_evidence_binds_capability_role_effect_and_skill_identity(
    tmp_path: Path, mutation: str, expected: str,
) -> None:
    value = valid_evidence()
    if mutation == "owner":
        value["owner_role"] = "CM"
    elif mutation == "leaf":
        value["producer_leaf"] = "hmasd-implementer"
    elif mutation == "candidate":
        value["capability"]["capability_id"] = "networkx"
    elif mutation == "skill-hash":
        value["capability"]["skill_ref"]["sha256"] = "0" * 64
    elif mutation == "effect":
        value["capability"]["effect_class"] = "external_read_only"
    elif mutation == "tool":
        value["capability"]["tool"] = "different-tool"
    elif mutation == "tool-version":
        value["capability"]["tool_version"] = "different-version"
    elif mutation == "invocation":
        value["invocation"] = {
            "kind": "command",
            "argv": [".agents/skills/hmasd-scientific-critical-thinking/SKILL.md"],
            "cwd": ".",
            "entrypoint_ref": {
                "path": ".agents/skills/hmasd-scientific-critical-thinking/SKILL.md",
                "sha256": sha256_path(CRITICAL_SKILL),
            },
        }
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert expected in result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("sidecar", "sidecar_path"),
        ("input-hash", "input_refs[0] sha256"),
        ("artifact-hash", "artifact sha256"),
    ],
)
def test_validate_evidence_authenticates_final_path_and_repo_content_hashes(
    tmp_path: Path, mutation: str, expected: str,
) -> None:
    value = valid_evidence()
    materialize_raw_observation(value)
    if mutation == "sidecar":
        value["sidecar_path"] = (
            "docs/research/candidates/field_slot_coordination/evidence/wrong.json"
        )
    elif mutation == "input-hash":
        value["frozen_operation"]["input_refs"][0]["sha256"] = "0" * 64
    elif mutation == "artifact-hash":
        value["artifacts"][0]["sha256"] = "0" * 64
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert expected in result.stderr


def test_validate_evidence_binds_raw_typed_observation_identity(tmp_path: Path) -> None:
    value = valid_evidence()
    value["evidence_id"] = "critical-thinking-field-slot-mismatch"
    value["sidecar_path"] = (
        "docs/research/candidates/field_slot_coordination/evidence/"
        "critical-thinking-field-slot-mismatch.json"
    )
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/instruments/"
        "critical-thinking-field-slot-mismatch/observation.json"
    )
    artifact = materialize_raw_observation(value)
    raw = json.loads(artifact.read_text(encoding="utf-8"))
    raw["instrument_observation"]["evidence_id"] = "different-evidence"
    artifact.write_text(json.dumps(raw), encoding="utf-8")
    value["artifacts"][0]["sha256"] = sha256_path(artifact)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )
    artifact.unlink()
    artifact.parent.rmdir()

    assert result.returncode == 2
    assert "typed observation identity" in result.stderr


def test_validate_evidence_binds_raw_core_observations(tmp_path: Path) -> None:
    value = valid_evidence()
    materialize_raw_observation(value)
    value["outcome"]["core_observations"] = ["Unbound manager-authored observation."]
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "core_observations" in result.stderr


def test_validate_evidence_rejects_candidate_outside_instrument_or_final_path(
    tmp_path: Path,
) -> None:
    value = valid_evidence()
    materialize_raw_observation(value)
    path = tmp_path / "external-candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "candidate path" in result.stderr


def test_validate_evidence_rejects_secret_like_raw_observation(tmp_path: Path) -> None:
    value = valid_evidence()
    value["evidence_id"] = "critical-thinking-field-slot-secret"
    value["sidecar_path"] = (
        "docs/research/candidates/field_slot_coordination/evidence/"
        "critical-thinking-field-slot-secret.json"
    )
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/instruments/"
        "critical-thinking-field-slot-secret/observation.json"
    )
    artifact = materialize_raw_observation(value)
    raw = json.loads(artifact.read_text(encoding="utf-8"))
    raw["instrument_observation"]["evidence_id"] = value["evidence_id"]
    raw["instrument_observation"]["OPENAI_API_KEY"] = "must-not-be-captured"
    artifact.write_text(json.dumps(raw), encoding="utf-8")
    value["artifacts"][0]["sha256"] = sha256_path(artifact)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )
    artifact.unlink()
    artifact.parent.rmdir()

    assert result.returncode == 2
    assert "secret-like" in result.stderr


def test_validate_evidence_rejects_unknown_raw_observation_fields(
    tmp_path: Path,
) -> None:
    value = valid_evidence()
    value["evidence_id"] = "critical-thinking-field-slot-unknown"
    value["sidecar_path"] = (
        "docs/research/candidates/field_slot_coordination/evidence/"
        "critical-thinking-field-slot-unknown.json"
    )
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/instruments/"
        "critical-thinking-field-slot-unknown/observation.json"
    )
    artifact = materialize_raw_observation(value)
    raw = json.loads(artifact.read_text(encoding="utf-8"))
    raw["instrument_observation"]["evidence_id"] = value["evidence_id"]
    raw["instrument_observation"]["scientific_acceptance"] = True
    artifact.write_text(json.dumps(raw), encoding="utf-8")
    value["artifacts"][0]["sha256"] = sha256_path(artifact)
    candidate = instrument_candidate_path(value, f"pytest-{tmp_path.name}.json")
    candidate.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(candidate),
        "--direction-id",
        "field_slot_coordination",
    )
    candidate.unlink()
    artifact.unlink()
    artifact.parent.rmdir()

    assert result.returncode == 2
    assert "typed observation schema" in result.stderr


def test_validate_evidence_rejects_minimal_untyped_observation(tmp_path: Path) -> None:
    value = valid_evidence()
    value["evidence_id"] = "critical-thinking-field-slot-minimal"
    value["sidecar_path"] = (
        "docs/research/candidates/field_slot_coordination/evidence/"
        "critical-thinking-field-slot-minimal.json"
    )
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/instruments/"
        "critical-thinking-field-slot-minimal/observation.json"
    )
    artifact = ROOT / value["artifacts"][0]["path"]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        json.dumps(
            {
                "instrument_observation": {
                    "evidence_id": value["evidence_id"],
                    "capability_id": "scientific-critical-thinking",
                    "outcome": "OBSERVED",
                    "core_observations": value["outcome"]["core_observations"],
                    "claim_ceiling": value["manager_interpretation"]["claim_ceiling"],
                }
            }
        ),
        encoding="utf-8",
    )
    value["artifacts"][0]["sha256"] = sha256_path(artifact)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )
    artifact.unlink()
    artifact.parent.rmdir()

    assert result.returncode == 2
    assert "typed observation schema" in result.stderr


def test_validate_evidence_accepts_typed_failed_operation_without_fake_audit(
    tmp_path: Path,
) -> None:
    value = valid_evidence()
    value["evidence_id"] = "critical-thinking-field-slot-failed"
    value["sidecar_path"] = (
        "docs/research/candidates/field_slot_coordination/evidence/"
        "critical-thinking-field-slot-failed.json"
    )
    value["outcome"] = {
        "status": "FAILED",
        "core_observations": ["The frozen audit failed before a claim observation."],
        "failure": {"code": "AUDIT_FAILED", "summary": "Synthetic failure fixture."},
    }
    value["manager_interpretation"]["impact_summary"] = (
        "The failed operation contributes no claim observation."
    )
    value["manager_interpretation"]["claim_ceiling"] = (
        "No scientific claim may be inferred from the failed operation."
    )
    value["artifacts"][0]["path"] = (
        "temp/directions/field_slot_coordination/test/instruments/"
        "critical-thinking-field-slot-failed/observation.json"
    )
    artifact = ROOT / value["artifacts"][0]["path"]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        json.dumps(
            {
                "instrument_observation": {
                    "schema_version": 1,
                    "evidence_id": value["evidence_id"],
                    "capability_id": "scientific-critical-thinking",
                    "outcome": "FAILED",
                    "core_observations": value["outcome"]["core_observations"],
                    "assumptions": [],
                    "limitations": ["No audit observation was produced."],
                    "claim_classification": None,
                    "source_facts": [],
                    "inferences": [],
                    "threats": [],
                    "strongest_alternative": None,
                    "decisive_missing_evidence": [],
                    "supported_claim": None,
                    "claim_ceiling": None,
                    "failure": value["outcome"]["failure"],
                }
            }
        ),
        encoding="utf-8",
    )
    value["artifacts"][0]["sha256"] = sha256_path(artifact)
    candidate = instrument_candidate_path(value, f"pytest-{tmp_path.name}.json")
    candidate.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(candidate),
        "--direction-id",
        "field_slot_coordination",
    )
    candidate.unlink()
    artifact.unlink()
    artifact.parent.rmdir()

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("missing", "schema error"),
        ("unknown", "schema error"),
        ("shell-string", "schema error"),
        ("traversal", "schema error"),
        ("absolute", "schema error"),
    ],
)
def test_validate_evidence_fails_closed_on_malformed_contracts(
    tmp_path: Path, mutation: str, expected: str,
) -> None:
    value = copy.deepcopy(valid_evidence())
    if mutation == "missing":
        del value["manager_interpretation"]
    elif mutation == "unknown":
        value["scientific_acceptance"] = True
    elif mutation == "shell-string":
        value["invocation"]["argv"] = "python probe.py --accept"
    elif mutation == "traversal":
        value["frozen_operation"]["input_refs"][0]["path"] = "../escape.md"
    elif mutation == "absolute":
        value["invocation"]["cwd"] = "C:/Projects/HMASD"
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert expected in result.stderr


@pytest.mark.parametrize("status", ["FAILED", "UNAVAILABLE"])
def test_validate_evidence_requires_failure_information_for_non_observation(
    tmp_path: Path, status: str,
) -> None:
    value = valid_evidence()
    value["outcome"]["status"] = status
    value["outcome"]["failure"] = None
    path = (
        tmp_path
        / "docs/research/candidates/field_slot_coordination/evidence"
        / f"{value['evidence_id']}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")

    result = run_cli(
        "validate-evidence",
        "--path",
        str(path),
        "--direction-id",
        "field_slot_coordination",
    )

    assert result.returncode == 2
    assert "schema error" in result.stderr
