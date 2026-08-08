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


def test_explorer_workflow_authority_is_centralized_and_transport_is_delegated() -> None:
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    transport_profile_path = REPO / ".codex" / "agents" / "hmasd-agentify-transport.toml"
    assert transport_profile_path.is_file()
    transport_profile = transport_profile_path.read_text(encoding="utf-8")
    skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    pro_review_skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-pro-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    workspace = (
        REPO / "docs" / "session-workspaces" / "independent_research_explorer" / "README.md"
    ).read_text(encoding="utf-8")
    wdm_role = (REPO / ".agents" / "roles" / "WORKFLOW_DESIGN_MANAGER.md").read_text(
        encoding="utf-8"
    )
    role_lines = set(role.splitlines())
    skill_normalized = " ".join(skill.split())
    pro_review_skill_normalized = " ".join(pro_review_skill.split())
    parallel_normalized = " ".join(parallel.split())
    for required in (
        "startup_identity=role|model|current_task",
        "workflow_authority=none",
        "workflow_modification_authority=none",
        "workflow_acceptance_authority=none",
        "workflow_git_authority=none",
        "workflow_change_request_route=workflow_design_manager",
        "git_authority=none",
        "current_work_read=read_only_as_needed_for_project_validation",
        "local_research_write_tool=apply_patch_only",
        "local_research_shell_mutation=forbidden",
        "continuity_entry=local_research/RESEARCH_CONTINUITY.md",
        "continuity_owner=independent_research_explorer",
        "public_handoff_outbound=temp/handoffs/explorer_to_code_manager/",
        "public_handoff_inbound_read=temp/handoffs/code_manager_to_explorer/",
        "public_handoff_git_authority=none",
        "public_handoff_admission=semantic_judgment_no_mandatory_schema",
        "project_validation_instruction_authority=authorize_cpm_named_treatment_execution",
        "project_validation_read_authority=project_wide_read_only_as_needed",
        "project_validation_semantic_acceptance_owner=external_pro",
        "project_validation_acceptance_review_request_and_intake=exclusive_for_explorer_origin",
        "project_validation_acceptance_review_mode=CODE_SCIENCE_ALIGNMENT_AUDIT",
        "project_validation_alignment_packet_effect=authoritative_scientific_semantic_acceptance",
        "cross_task_transport=codex_native_send_message_to_thread",
        "cross_task_target=current_thread_id_from_user_or_native_task_context",
        "cross_task_model_and_thinking_overrides=omit",
        "independent_pro_review_assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:",
        "independent_pro_review_item_root=local_research/pro_reviews/<review-id>/",
        "independent_pro_review_request_and_intake_authority=exclusive_for_explorer_direction_and_methodology_reviews",
        "agentify_transport_child=hmasd-agentify-transport",
        "agentify_transport_parent=independent_research_explorer",
        "agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT",
        "agentify_transport_assignment_fields=batch_path|results_path",
        "agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT",
        "agentify_transport_result_fields=status|results_path|error",
        "agentify_transport_terminal_status=COMPLETE|ERROR",
        "agentify_transport_wait_visibility=silent_until_terminal_native_final",
        "independent_pro_review_transport_execution=registered_agentify_transport_child",
        "independent_review_provider_contract=agentify_file_batch_result",
        "independent_review_transmitted_payload=standalone_RAW_QUESTION_only",
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
    assert "centralized_explorer_workflow_paths=" not in wdm_role
    assert "workflow_authority=exclusive_for_owned_surfaces" not in role_lines
    assert "git_authority=direct_for_owned_workflow_surfaces" not in role_lines
    assert not any(line.startswith("session_id=") for line in role_lines)

    for required in (
        "Workflow design is not an Explorer mode.",
        "Report one exact requirement or defect to the current Workflow Design Manager task",
        "never load the collaborative/audit Workflow Skills",
        "one minimal batch file containing provider and the ordered paths",
        "AGENTIFY_REVIEW_BATCH_RESULT",
        "currently eligible frozen questions",
        "no archived task ID or route registry",
        "one bounded owned-path scan",
        "registered `hmasd-agentify-transport` child",
        "AGENTIFY_REVIEW_BATCH_ASSIGNMENT",
        "batch_path|results_path",
        "silent while live",
        "exactly once through its native final response",
        "status|results_path|error",
        "terminal status `COMPLETE|ERROR`",
        "no polling, progress handling or parent-task result relay",
    ):
        assert required in skill_normalized
    assert "$hmasd-collaborative-workflow-design" not in skill
    assert "$hmasd-workflow-change-audit" not in skill

    for required in (
        "invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`",
        "there is no separate persistent review-operator session",
        "dispatch one self-contained",
        "`AGENTIFY_REVIEW_BATCH_ASSIGNMENT`",
        "registered `hmasd-agentify-transport` child",
        "batch_path|results_path",
        "silent while live",
        "exactly once through its native final response",
        "status|results_path|error",
        "terminal status `COMPLETE|ERROR`",
        "no polling, progress handling or parent-task result relay",
        "Copy each named successful raw response",
    ):
        assert required in pro_review_skill_normalized
    assert "hmasd-independent-research-pro" not in pro_review_skill.replace(
        "hmasd-independent-research-pro-review", ""
    )

    assert "IR_DIRECTION_REVIEW:" in pro_review_skill
    assert "IR_METHODOLOGY_REVIEW:" in pro_review_skill
    assert "local_research/pro_reviews/<review-id>/" in pro_review_skill
    assert "IR_UNSUPPORTED_REVIEW:" not in pro_review_skill
    assert "independent_pro_direction_transport_authority=" not in role
    assert "independent_pro_direction_transport_execution=" not in role
    assert "independent_pro_direction_stable_key=" not in role
    assert "independent_pro_direction_terminal_intake=" not in role
    assert "registered_provision_direction" not in role
    assert "registered_provision_review" not in role
    for required in (
        'name = "hmasd-agentify-transport"',
        'model = "gpt-5.6-luna"',
        'model_reasoning_effort = "medium"',
    ):
        assert required in transport_profile
    for surface in (role, skill, pro_review_skill):
        for retired in (
            "return_task_id",
            "dedicated Agentify task",
            "dedicated transport task",
            "cross-task return",
            "AGENTIFY_REVIEW_BATCH_REQUEST",
        ):
            assert retired not in surface

    for required in (
        "restart_identity=role|model|current_task",
        "continuity_entry=local_research/RESEARCH_CONTINUITY.md",
        "last completed phase barrier",
        "unfinished assignment or review",
        "next scientific action",
        "current authorized source boundary",
        "Update it only at phase barriers, parked state or task end.",
        "one bounded scan",
    ):
        assert required in parallel_normalized

    for required in (
        "session_owner_role=independent_research_explorer",
        "startup_identity=role|model|current_task",
        "continuity_entry=local_research/RESEARCH_CONTINUITY.md",
        "durable_workspace=docs/session-workspaces/independent_research_explorer/",
        "temporary_workspace=temp/sessions/independent_research_explorer/",
        "shared_surface_owner=false",
        "public_current_work_partition_authority=none",
        "docs/project/handoffs/README.md",
    ):
        assert required in workspace


def test_scientific_only_intake_boundary_uses_one_explorer_decision_record() -> None:
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    validation_skill = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-explorer-project-validation"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    exploration_skill = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    contract = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    handoffs = (REPO / "docs" / "project" / "handoffs" / "README.md").read_text(
        encoding="utf-8"
    )

    normalized_contract = " ".join(contract.split())
    for required in (
        "CPM's mechanically verified packet",
        "does not recompute schema, readability, receipts, activity counts, locators",
        "scientifically ambiguous",
        "supported proposition",
        "strongest alternative explanation",
        "information gain",
        "next discriminator",
        "A/B/C or named-Pro action",
        "one canonical scientific decision record",
        "existing `local_research/` ownership",
        "Portfolio, index, README and continuity",
        "pointer, navigation",
        "mandatory packet schema or validator admission gate",
        "ordinary B",
        "named Pro triggers",
    ):
        assert required in normalized_contract, f"missing defining intake clause: {required}"

    pointer = "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    for surface in (role, validation_skill, exploration_skill, parallel, handoffs):
        assert pointer in surface, "scientific-only intake surface must point to its single source"

    assert "project_validation_intake_boundary=scientific_only_after_cpm_technical_acceptance" in role
    assert "project_validation_technical_recompute=forbidden_unless_scientifically_ambiguous" in role
    assert "canonical_scientific_decision_record=one_per_candidate_under_existing_local_research_ownership" in role
    assert "portfolio_index_readme_continuity_role=pointer_navigation_barrier_only" in role
    assert "does not invoke External Pro" in " ".join(contract.split())


def test_direction_local_context_binding_is_symmetric_and_preserves_artifacts() -> None:
    contract = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    explorer_role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    cpm_role = (REPO / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md").read_text(
        encoding="utf-8"
    )
    cpm_role_normalized = " ".join(cpm_role.split())
    exploration_skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    validation_skill = (
        REPO / ".agents" / "skills" / "hmasd-explorer-project-validation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    validation_skill_normalized = " ".join(validation_skill.split())
    handoffs = (REPO / "docs" / "project" / "handoffs" / "README.md").read_text(
        encoding="utf-8"
    )
    workflow_map = (REPO / "docs" / "project" / "WORKFLOW_MAP.md").read_text(encoding="utf-8")

    normalized_contract = " ".join(contract.split())
    for required in (
        "direction-specific Explorer answer",
        "selected direction identity",
        "canonical decision/source context",
        "parent, child or cross-direction",
        "preloading or merging the whole portfolio",
        "candidate and exact current proposition",
        "source/evidence revision boundary",
        "explicit exclusion of sibling-direction generalization",
        "one requested action and its direct consumer",
        "CPM's reverse result begins with its conclusion",
        "mirrors that same primary direction or explicitly named direction set",
        "Codex-native message fallback carries the same binding and content",
        "preserves the original handoff/artifact",
        "asks exactly one concrete semantic clarification",
        "creates a `BLOCKED` state",
        "pointer-only",
    ):
        assert required in normalized_contract

    pointer = "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    for surface in (explorer_role, exploration_skill, parallel, validation_skill, handoffs):
        assert pointer in surface

    for required in (
        "selected direction",
        "smallest set",
        "sibling",
        "semantic clarification",
    ):
        assert required in explorer_role
        assert required in cpm_role_normalized

    assert "explicitly multi-direction user question" in normalized_contract
    assert "never imports another direction" in normalized_contract
    assert "portfolio-wide meaning" in normalized_contract
    assert "A Codex-native message fallback carries the same binding" in handoffs
    assert "never preload or merge unrequested siblings" in exploration_skill
    assert "preserve the original handoff/artifact" in validation_skill_normalized
    assert "direction-local context binding" in workflow_map
    assert "never reads `local_research/`" in cpm_role_normalized
