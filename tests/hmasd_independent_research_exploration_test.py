from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO
    / ".agents"
    / "skills"
    / "hmasd-independent-research-exploration"
    / "scripts"
    / "mylib_research_probe.py"
)


def make_library(tmp_path: Path) -> Path:
    root = tmp_path / "MyLib"
    for name in ("metadata", "llm-index", "pdf", "json", "assets"):
        (root / name).mkdir(parents=True)
    (root / "metadata" / "v2").mkdir()
    integrity = {
        "actual": {"json": 1, "pdf": 2, "records": 2},
        "content_contract": "pdf+json+metadata+llm-index",
        "expected": {"json": 1, "pdf": 2, "records": 2},
        "duplicate_ids": [],
        "missing_json_ids": ["MARL-0002"],
        "metadata_v2": {
            "catalog": "papers/MyLib/llm-index/catalog.v2.jsonl",
            "full_json": "papers/MyLib/metadata/v2/papers.v2.json",
            "full_jsonl": "papers/MyLib/metadata/v2/papers.v2.jsonl",
            "quality_grades": {"A": 1, "B": 1},
            "quality_report": "papers/MyLib/metadata/v2/quality-report.v2.json",
            "records": 2,
            "schema": "papers/MyLib/metadata/v2/schema.v2.json",
            "status": "validated",
        },
    }
    (root / "metadata" / "integrity.json").write_text(
        json.dumps(integrity), encoding="utf-8"
    )
    catalog_records = [
        {
            "id": "MARL-0001",
            "title": "Recurrent Coordination",
            "abstract": "memory and changing teams",
            "algorithm_names": ["GRU"],
            "method_family": ["recurrent-policy"],
            "marl_setting": ["cooperative"],
            "benchmarks": ["roster shift"],
            "keywords": ["dynamic teams"],
            "pdf_path": "MyLib/pdf/MARL-0001.pdf",
            "json_path": "MyLib/json/MARL-0001.json",
            "quality_grade": "A",
            "quality_score": 100,
            "semantic_status": "luna_json_abstract_grounded",
        },
        {
            "id": "MARL-0002",
            "title": "Roster Counterexample",
            "abstract": "join leave failure",
            "algorithm_names": [],
            "method_family": ["unspecified"],
            "marl_setting": ["unspecified"],
            "benchmarks": [],
            "keywords": ["counterexample"],
            "pdf_path": "MyLib/pdf/MARL-0002.pdf",
            "json_path": "",
            "quality_grade": "B",
            "quality_score": 80,
            "semantic_status": "luna_official_abstract_grounded",
        },
    ]
    (root / "llm-index" / "catalog.v2.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in catalog_records),
        encoding="utf-8",
    )
    (root / "llm-index" / "catalog.jsonl").write_text(
        json.dumps({"id": "LEGACY-ONLY", "title": "must not be read"}) + "\n",
        encoding="utf-8",
    )
    full_records = [
        {
            "schema_version": "2.0",
            "id": "MARL-0001",
            "bibliographic": {"title": "Recurrent Coordination"},
            "abstract": {"text": "memory and changing teams"},
            "assets": {
                "json_path": "MyLib/json/MARL-0001.json",
                "pdf_path": "MyLib/pdf/MARL-0001.pdf",
            },
            "research": {
                "method_family": ["recurrent-policy"],
                "limitations": ["roster shift remains unverified"],
            },
            "provenance": {
                "field_evidence": {
                    "abstract": {
                        "source": "official_citation_meta",
                        "url": "https://example.test/MARL-0001",
                    },
                    "research": {
                        "source_field": "abstract.text",
                        "evidence_path": "MyLib/json/MARL-0001.json",
                        "confidence": 0.82,
                    },
                }
            },
            "quality": {
                "grade": "A",
                "warnings": [],
                "semantic_status": "luna_json_abstract_grounded",
                "json_status": "json_ready",
            },
        },
        {
            "schema_version": "2.0",
            "id": "MARL-0002",
            "bibliographic": {"title": "Roster Counterexample"},
            "abstract": {"text": "join leave failure"},
            "assets": {
                "json_path": "",
                "pdf_path": "MyLib/pdf/MARL-0002.pdf",
            },
            "research": {
                "method_family": ["unspecified"],
                "limitations": [],
            },
            "provenance": {
                "field_evidence": {
                    "abstract": {
                        "source": "official_abstract",
                        "url": "https://example.test/MARL-0002",
                    },
                    "research": {
                        "source_field": "abstract.text",
                        "evidence_path": "https://example.test/MARL-0002",
                        "evidence_url": "https://example.test/MARL-0002",
                        "caveats": ["abstract_only"],
                        "confidence": 0.70,
                    },
                }
            },
            "quality": {
                "grade": "B",
                "warnings": ["structured_json_missing"],
                "semantic_status": "luna_official_abstract_grounded",
                "json_status": "missing",
            },
        },
    ]
    (root / "metadata" / "v2" / "papers.v2.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in full_records),
        encoding="utf-8",
    )
    (root / "metadata" / "v2" / "papers.v2.json").write_text(
        json.dumps(full_records), encoding="utf-8"
    )
    (root / "metadata" / "v2" / "schema.v2.json").write_text(
        json.dumps({"type": "object", "required": ["id", "quality", "provenance"]}),
        encoding="utf-8",
    )
    (root / "metadata" / "v2" / "quality-report.v2.json").write_text(
        json.dumps({"records": 2, "quality_grades": {"A": 1, "B": 1}}),
        encoding="utf-8",
    )
    (root / "llm-index" / "titles.tsv").write_text(
        "id\ttitle\nMARL-0001\tRecurrent Coordination\n"
        "MARL-0002\tRoster Counterexample\n",
        encoding="utf-8",
    )
    for paper_id in ("MARL-0001", "MARL-0002"):
        (root / "pdf" / f"{paper_id}.pdf").write_bytes(
            b"%PDF-1.4\nfixture\n%%EOF\n"
        )
    (root / "json" / "MARL-0001.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page": 1,
                        "elements": [
                            {
                                "type": "paragraph",
                                "text": "Recurrent memory is not sufficient evidence.",
                                "bbox": [10, 20, 300, 80],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return root


def run_cli(
    mylib: Path,
    local_research: Path,
    *args: str,
    expected: int = 0,
    claimed_local_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    copied_script = (
        local_research.parent
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "scripts"
        / "mylib_research_probe.py"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(copied_script),
            "--mylib-root",
            str(mylib),
            "--local-research-root",
            str(claimed_local_root or local_research),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == expected, completed.stderr or completed.stdout
    return completed


def make_local_research(tmp_path: Path) -> Path:
    local_research = tmp_path / "repo" / "local_research"
    copied_script = (
        local_research.parent
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "scripts"
        / "mylib_research_probe.py"
    )
    copied_script.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, copied_script)
    local_research.mkdir(parents=True)
    return local_research


def payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(completed.stdout)


def mutate_full_record(mylib: Path, paper_id: str, mutation: str) -> None:
    path = mylib / "metadata" / "v2" / "papers.v2.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    record = next(item for item in records if item["id"] == paper_id)
    research = record["provenance"]["field_evidence"]["research"]
    if mutation == "remove_abstract_only":
        research["caveats"] = []
    elif mutation == "empty_evidence_url":
        research["evidence_url"] = ""
    else:
        raise AssertionError(f"unknown fixture mutation: {mutation}")
    path.write_text(
        "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
    )


def test_status_uses_live_integrity_instead_of_hard_coded_counts(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(run_cli(mylib, local_research, "status"))
    assert result["actual"] == {"json": 1, "pdf": 2, "records": 2}
    assert result["content_contract"] == "pdf+json+metadata+llm-index"
    assert result["missing_json_ids"] == ["MARL-0002"]
    assert result["metadata_v2"]["status"] == "validated"
    assert result["metadata_v2"]["quality_grades"] == {"A": 1, "B": 1}


def test_search_is_v2_recall_only_and_exposes_quality_and_provenance(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(
        run_cli(mylib, local_research, "search", "--query", "memory", "--limit", "1")
    )
    assert result["evidence_authority"] == "discovery_only"
    assert result["semantic_scope"] == "title_or_abstract_only"
    assert result["results"] == [
        {
            "id": "MARL-0001",
            "title": "Recurrent Coordination",
            "quality_grade": "A",
            "quality_warnings": [],
            "semantic_status": "luna_json_abstract_grounded",
            "provenance_field_evidence": {
                "abstract": {
                    "source": "official_citation_meta",
                    "url": "https://example.test/MARL-0001",
                },
                "research": {
                    "source_field": "abstract.text",
                    "evidence_path": "MyLib/json/MARL-0001.json",
                    "confidence": 0.82,
                },
            },
            "metadata_path": str(mylib / "metadata" / "v2" / "papers.v2.jsonl"),
            "json_path": str(mylib / "json" / "MARL-0001.json"),
            "pdf_path": str(mylib / "pdf" / "MARL-0001.pdf"),
        }
    ]


def test_search_uses_abstract_grounded_facets_only_for_recall(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(
        run_cli(
            mylib,
            local_research,
            "search",
            "--query",
            "roster shift",
            "--limit",
            "2",
        )
    )
    assert result["evidence_authority"] == "discovery_only"
    assert result["empty_or_unspecified_are_unknown"] is True
    assert [item["id"] for item in result["results"]] == ["MARL-0001"]


def test_legacy_catalog_is_not_a_registered_recall_source(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(
        run_cli(mylib, local_research, "search", "--query", "must not be read")
    )
    assert result["results"] == []


def test_locate_routes_json_missing_paper_directly_to_pdf(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(
        run_cli(mylib, local_research, "locate", "--paper-id", "MARL-0002")
    )
    assert result["json_missing"] is True
    assert result["content_entry"] == "pdf"
    assert result["detail_verification_entry"] == "pdf"
    assert result["abstract_only"] is True
    assert result["evidence_url"] == "https://example.test/MARL-0002"
    assert result["quality"]["grade"] == "B"
    assert result["quality"]["warnings"] == ["structured_json_missing"]
    assert result["provenance_field_evidence"]["abstract"]["url"] == (
        "https://example.test/MARL-0002"
    )
    assert result["pdf"]["exists"] is True
    assert result["legacy_markdown_allowed"] is False


def test_missing_json_requires_explicit_abstract_only_and_nonempty_evidence_url(
    tmp_path: Path,
) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    mutate_full_record(mylib, "MARL-0002", "remove_abstract_only")
    missing_marker = payload(
        run_cli(
            mylib,
            local_research,
            "locate",
            "--paper-id",
            "MARL-0002",
            expected=2,
        )
    )
    assert "explicit abstract_only provenance" in str(missing_marker["error"])

    mylib = make_library(tmp_path / "second")
    local_research = make_local_research(tmp_path / "second")
    mutate_full_record(mylib, "MARL-0002", "empty_evidence_url")
    missing_url = payload(
        run_cli(
            mylib,
            local_research,
            "locate",
            "--paper-id",
            "MARL-0002",
            expected=2,
        )
    )
    assert "nonempty evidence_url" in str(missing_url["error"])


def test_validate_pdf_rejects_truncated_source(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    good = payload(
        run_cli(mylib, local_research, "validate-pdf", "--paper-id", "MARL-0001")
    )
    assert good["valid"] is True
    (mylib / "pdf" / "MARL-0001.pdf").write_bytes(b"%PDF-1.4\ntruncated")
    bad = payload(
        run_cli(
            mylib,
            local_research,
            "validate-pdf",
            "--paper-id",
            "MARL-0001",
            expected=2,
        )
    )
    assert bad["valid"] is False
    assert bad["reason"] == "missing_pdf_eof"


def test_output_is_confined_to_local_research(tmp_path: Path) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    receipt = local_research / "smoke.json"
    run_cli(mylib, local_research, "status", "--output", str(receipt))
    assert receipt.is_file()

    forbidden = mylib / "metadata" / "forbidden.json"
    run_cli(
        mylib,
        local_research,
        "status",
        "--output",
        str(forbidden),
        expected=2,
    )
    assert not forbidden.exists()

    wrong_root = payload(
        run_cli(
            mylib,
            local_research,
            "status",
            expected=2,
            claimed_local_root=mylib,
        )
    )
    assert "registered checkout directory" in str(wrong_root["error"])


def test_smoke_reads_integrity_catalog_json_and_a_traceable_pdf(
    tmp_path: Path,
) -> None:
    mylib = make_library(tmp_path)
    local_research = make_local_research(tmp_path)
    result = payload(run_cli(mylib, local_research, "smoke"))
    assert result["status"] == "MYLIB_READ_ONLY_SMOKE_OK"
    assert result["paper_id"] == "MARL-0001"
    assert result["json_valid"] is True
    assert result["core_text_field_count"] == 1
    assert result["json_access_layer"] is True
    assert result["pdf_valid"] is True
    assert result["metadata_v2_validated"] is True
    assert result["quality_grade"] == "A"
    assert result["provenance_checked"] is True
    assert result["legacy_markdown_allowed"] is False


def test_open_inspiration_reference_preserves_source_first_dynamic_portfolio() -> None:
    skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    pro_review_skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-pro-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    reference = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "open-algorithm-inspiration.md"
    ).read_text(encoding="utf-8")
    for required in (
        "algorithm inspiration campaign",
        "SOURCE_RESULT_PACKET",
        "RL_PRINCIPLE_ANALYSIS_PACKET",
        "NEXT_CYCLE_OPPORTUNITY_MAP",
        "available native capacity",
    ):
        assert required in skill
    for required in (
        "source_result",
        "transferable_primitive",
        "adaptation_hypothesis",
        "algorithm_candidate",
        "subdirection_split",
        "cross_direction_inspiration",
    ):
        assert required in reference


def test_explorer_workflow_authority_is_centralized_and_transport_is_direct() -> None:
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    pro_review_skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-pro-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    pro_review_transport = (
        REPO
        / "docs"
        / "session-workspaces"
        / "independent_research_explorer"
        / "PRO_REVIEW_TRANSPORT.md"
    ).read_text(encoding="utf-8")
    workspace = (
        REPO / "docs" / "session-workspaces" / "independent_research_explorer" / "README.md"
    ).read_text(encoding="utf-8")
    wdm_role = (REPO / ".agents" / "roles" / "WORKFLOW_DESIGN_MANAGER.md").read_text(
        encoding="utf-8"
    )
    role_lines = set(role.splitlines())
    skill_normalized = " ".join(skill.split())
    exact_owned_paths = (
        "centralized_explorer_workflow_paths=.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md|"
        ".agents/skills/hmasd-independent-research-exploration/SKILL.md|"
        ".agents/skills/hmasd-explorer-project-validation/SKILL.md|"
        ".agents/skills/hmasd-independent-research-pro-review/SKILL.md|"
        "tests/hmasd_independent_research_exploration_test.py|"
        "tests/hmasd_explorer_project_validation_packet_test.py|"
        "tests/hmasd_research_workflow_contract_test.ps1|"
        "docs/session-workspaces/independent_research_explorer/README.md|"
        "docs/session-workspaces/independent_research_explorer/PRO_REVIEW_TRANSPORT.md"
    )

    for required in (
        "session_id=019fbded-24cb-7541-aa16-0111b626b945",
        "workflow_authority=none",
        "workflow_modification_authority=none",
        "workflow_acceptance_authority=none",
        "workflow_git_authority=none",
        "workflow_change_request_route=workflow_design_manager",
        "git_authority=none",
        "current_work_read=forbidden",
        "local_research_write_tool=apply_patch_only_except_registered_provision_and_agentify_review_lifecycle",
        "local_research_shell_mutation=forbidden_except_registered_provision_and_agentify_review_lifecycle",
        "independent_pro_review_assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:",
        "independent_pro_review_provision_command=provision-direction",
        "independent_pro_review_item_root=local_research/pro_reviews/<review-id>/",
        "independent_pro_review_transport_authority=exclusive_for_explorer_direction_and_methodology_reviews",
        "independent_pro_review_transport_execution=persistent_explorer_session_direct",
        "independent_pro_review_stable_key=hmasd-independent-research-explorer-pro",
        "independent_pro_review_terminal_intake=exact_archived_response_fifo",
    ):
        assert required in role
    prefix_line = next(
        line for line in role_lines if line.startswith("independent_pro_review_assignment_prefixes=")
    )
    supported_prefixes = tuple(prefix_line.split("=", 1)[1].split("|"))
    assert supported_prefixes == ("IR_DIRECTION_REVIEW:", "IR_METHODOLOGY_REVIEW:")
    for assignment in ("IR_DIRECTION_REVIEW:direction-1", "IR_METHODOLOGY_REVIEW:method-1"):
        assert assignment.startswith(supported_prefixes)
    for unsupported in (
        "IR_UNSUPPORTED_REVIEW:item-1",
        "IR_DIRECTION_REVIEW",
        "IR_METHODOLOGY_REVIEW",
        "PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW:item-1",
    ):
        assert not unsupported.startswith(supported_prefixes)
    assert exact_owned_paths in set(wdm_role.splitlines())
    assert "workflow_authority=exclusive_for_owned_surfaces" not in role_lines
    assert "git_authority=direct_for_owned_workflow_surfaces" not in role_lines

    for required in (
        "Workflow design is not an Explorer mode.",
        "Report one exact requirement or defect to Workflow Design Manager",
        "never load the collaborative/audit Workflow Skills",
        "persistent Explorer session directly performs each exact External Pro direction turn",
        "prepare -> submit -> verify -> archive",
        "No review/monitor child",
        "No hash, digest, fingerprint or byte count is a workflow predicate.",
    ):
        assert required in skill_normalized
    assert "$hmasd-collaborative-workflow-design" not in skill
    assert "$hmasd-workflow-change-audit" not in skill

    for required in (
        "invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`",
        "there is no separate persistent review-operator session",
        "stable_key=hmasd-independent-research-explorer-pro",
        "execution=persistent_explorer_session_direct",
        "archive",
        "local FIFO",
        "No hash, digest, fingerprint or byte count is a workflow predicate.",
    ):
        assert required in pro_review_skill
    assert "hmasd-independent-research-pro" not in pro_review_skill.replace(
        "hmasd-independent-research-pro-review", ""
    )

    for contract in (pro_review_skill, pro_review_transport):
        assert "IR_DIRECTION_REVIEW:" in contract
        assert "IR_METHODOLOGY_REVIEW:" in contract
        assert "provision-direction" in contract
        assert "local_research/pro_reviews/<review-id>/" in contract
        assert "IR_UNSUPPORTED_REVIEW:" not in contract
    assert "independent_pro_direction_transport_authority=" not in role
    assert "independent_pro_direction_transport_execution=" not in role
    assert "independent_pro_direction_stable_key=" not in role
    assert "independent_pro_direction_terminal_intake=" not in role
    assert "registered_provision_direction" not in role
    assert "registered_provision_review" not in role

    for required in (
        "session_owner_role=independent_research_explorer",
        "session_owner_id=019fbded-24cb-7541-aa16-0111b626b945",
        "durable_workspace=docs/session-workspaces/independent_research_explorer/",
        "temporary_workspace=temp/sessions/independent_research_explorer/",
        "shared_surface_owner=false",
        "public_current_work_partition_authority=none",
    ):
        assert required in workspace
