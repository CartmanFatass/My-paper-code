"""Current portfolio and direction contract tests."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
PORTFOLIO = ROOT / "docs" / "research" / "portfolio"
REGISTRY_PATH = PORTFOLIO / "workflow" / "registry.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_portfolio"

EXPECTED_IDS = (
    "active_post_churn_population_flow_identification",
    "acvc",
    "commitment_residual_triggered_options",
    "covariance_calibrated_information_clock",
    "degraded_incumbent_shadow_handover",
    "dual_epoch_receipt_survival",
    "ec4g_r1",
    "eociv_lite",
    "event_triggered_budgeted_cooperative_renewal",
    "expressibility_gated_renewal_credit_relay",
    "field_slot_coordination",
    "finite_semantic_boundary_support",
    "metric_ground_transport_allocation",
    "opportunity_normalized_lease_gated_rebinding",
    "optimizer_entropy_exposure_boundary_relay",
    "orbit_shadow_read",
    "recct_lite",
    "renewal_indexed_score_plasticity",
    "roster_consistent_latent_exploration",
    "roster_smf",
    "scope_1s",
    "semantic_graphon_shared_policy",
    "semigroup_consistent_duration_model_policy",
    "ucope",
    "vap_folr_core",
    "variable_n_fleet_churn",
    "voronoi_quadrature_field_policy",
    "vsp_02",
    "vsp_03",
    "vsp_04",
    "vsp_05",
    "vsp_06_mssr",
    "vsp_c1",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_worktree_changes(*paths: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", *(str(path.relative_to(ROOT)) for path in paths)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return bool(result.stdout)


def test_registry_preserves_stable_ids_and_validates_live_contract() -> None:
    registry = load_json(REGISTRY_PATH)
    assert tuple(direction["id"] for direction in registry["directions"]) == EXPECTED_IDS
    assert len(registry["directions"]) == len(EXPECTED_IDS)
    assert sum(direction["lifecycle"] == "ACTIVE" for direction in registry["directions"]) <= 8
    assert {direction["lifecycle"] for direction in registry["directions"]} <= {
        "REGISTERED", "ACTIVE", "PARKED", "CLOSED"
    }
    assert all(direction["dependencies"] == [] for direction in registry["directions"])

    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(REGISTRY_PATH))
    assert result.returncode == 0, result.stderr


def test_clean_direction_authority_and_states_reconcile_to_registry() -> None:
    registry = load_json(REGISTRY_PATH)
    assert sha256(PORTFOLIO / "PORTFOLIO.md") == registry["goal"]["sha256"]
    validated_directions: list[str] = []

    for direction in registry["directions"]:
        direction_id = direction["id"]
        candidate = ROOT / "docs" / "research" / "candidates" / direction_id
        authority = candidate / "DIRECTION.md"
        assert authority.is_file()
        research_path = ROOT / direction["research_state_path"]
        engineering_path = ROOT / direction["engineering_state_path"]
        external_path = ROOT / direction["external_review_index_path"]
        if has_worktree_changes(authority, research_path, engineering_path, external_path):
            # Shared main may contain another owner's exact in-progress paths.
            # Cross-file equality is meaningful only at a committed boundary.
            continue
        assert direction["lifecycle_decision_ref"]["sha256"] == sha256(PORTFOLIO / "PORTFOLIO.md")
        authority_text = authority.read_text(encoding="utf-8")
        assert "## Scientific question" in authority_text
        assert "## Provenance boundary" in authority_text
        for kind, path in (
            ("research_state", research_path),
            ("engineering_state", engineering_path),
            ("external_review_index", external_path),
        ):
            assert path.is_file(), (direction_id, kind)
            result = run_cli("validate", "--kind", kind, "--path", str(path))
            assert result.returncode == 0, (direction_id, kind, result.stderr)

        research = load_json(research_path)
        engineering = load_json(engineering_path)
        external = load_json(external_path)
        authority_sha = sha256(authority)
        assert research["direction_id"] == direction_id
        assert research["writer"] == f"EM-{direction_id}"
        assert research["phase"] in {
            "SCOPING",
            "DIVERGENT_REVIEW",
            "LOCAL_RESEARCH",
            "SYNTHESIS",
            "CONVERGENCE",
            "ENGINEERING_REQUESTED",
            "WAITING",
            "IDLE",
            "COMPLETE",
        }
        assert isinstance(research["actionable"], bool)
        assert research["direction_ref"] == {
            "path": f"docs/research/candidates/{direction_id}/DIRECTION.md",
            "sha256": authority_sha,
        }
        assert engineering["direction_id"] == direction_id
        assert engineering["writer"] == f"CM-{direction_id}"
        assert engineering["phase"] in {
            "UNREQUESTED",
            "SCOPING",
            "IMPLEMENTING",
            "VERIFYING",
            "RUN_READY",
            "RUNNING",
            "INTEGRATING",
            "WAITING",
            "COMPLETE",
            "FAILED",
        }
        assert isinstance(engineering["actionable"], bool)
        assert engineering["scope_ref"]["path"] == research["direction_ref"]["path"]
        assert len(engineering["scope_ref"]["sha256"]) == 64
        assert external["direction_id"] == direction_id
        assert external["writer"] == f"EM-{direction_id}"
        assert isinstance(external["rounds"], list)
        validated_directions.append(direction_id)

    assert validated_directions


def test_registry_rejects_duplicate_ids_abbreviations_paths_and_jobs(tmp_path: Path) -> None:
    source = load_json(FIXTURES / "portfolio_registry.json")
    first = source["directions"][0]
    mutations = {
        "id": ("id", first["id"]),
        "abbreviation": ("abbreviation", first["abbreviation"]),
        "path": ("path", first["path"]),
        "job": ("agent.job_name", first["agent"]["job_name"]),
    }
    for label, (field, value) in mutations.items():
        candidate = copy.deepcopy(source)
        if field == "agent.job_name":
            candidate["directions"][1]["agent"]["job_name"] = value
        else:
            candidate["directions"][1][field] = value
        path = tmp_path / f"duplicate-{label}.json"
        write_json(path, candidate)
        result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(path))
        assert result.returncode == 2, (label, result.stderr)


def test_registry_rejects_dependency_cycles_and_more_than_eight_active(tmp_path: Path) -> None:
    source = load_json(FIXTURES / "portfolio_registry.json")
    cyclic = copy.deepcopy(source)
    cyclic["directions"][0]["dependencies"] = [cyclic["directions"][1]["id"]]
    cyclic["directions"][1]["dependencies"] = [cyclic["directions"][0]["id"]]
    cyclic_path = tmp_path / "cycle.json"
    write_json(cyclic_path, cyclic)
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(cyclic_path))
    assert result.returncode == 2, result.stderr

    overflow = copy.deepcopy(source)
    for direction in overflow["directions"][:9]:
        direction["lifecycle"] = "ACTIVE"
    overflow_path = tmp_path / "active-overflow.json"
    write_json(overflow_path, overflow)
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(overflow_path))
    assert result.returncode == 2, result.stderr


def test_state_reconciliation_rejects_stale_missing_and_inconsistent_refs(tmp_path: Path) -> None:
    source = load_json(FIXTURES / "research_state.json")

    stale = copy.deepcopy(source)
    stale["direction_ref"]["sha256"] = "0" * 64
    stale_path = tmp_path / "stale.json"
    write_json(stale_path, stale)
    result = run_cli("validate", "--kind", "research_state", "--path", str(stale_path))
    assert result.returncode == 2, result.stderr

    missing = copy.deepcopy(source)
    missing["direction_ref"]["path"] = "docs/research/candidates/missing-direction/DIRECTION.md"
    missing_path = tmp_path / "missing.json"
    write_json(missing_path, missing)
    result = run_cli("validate", "--kind", "research_state", "--path", str(missing_path))
    assert result.returncode == 5, result.stderr

    inconsistent = copy.deepcopy(source)
    inconsistent["direction_id"] = "acvc"
    inconsistent_path = tmp_path / "inconsistent.json"
    write_json(inconsistent_path, inconsistent)
    result = run_cli("validate", "--kind", "research_state", "--path", str(inconsistent_path))
    assert result.returncode == 5, result.stderr


def test_registry_replacement_requires_portfolio_writer_and_expected_revision(tmp_path: Path) -> None:
    target = tmp_path / "registry.json"
    target.write_bytes(REGISTRY_PATH.read_bytes())
    replacement = load_json(REGISTRY_PATH)
    replacement["revision"] = 2
    replacement_path = tmp_path / "replacement.json"
    write_json(replacement_path, replacement)

    wrong_writer = run_cli(
        "replace",
        "--kind",
        "portfolio_registry",
        "--path",
        str(target),
        "--writer",
        "CM-acvc",
        "--expected-revision",
        "1",
        "--input",
        str(replacement_path),
    )
    assert wrong_writer.returncode == 5, wrong_writer.stderr

    stale_revision = run_cli(
        "replace",
        "--kind",
        "portfolio_registry",
        "--path",
        str(target),
        "--writer",
        "Portfolio",
        "--expected-revision",
        "0",
        "--input",
        str(replacement_path),
    )
    assert stale_revision.returncode == 4, stale_revision.stderr
