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
        "NEXT_CYCLE_OPPORTUNITY_MAP",
        "available native capacity",
    ):
        assert required in skill
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    assert "RL_PRINCIPLE_ANALYSIS_PACKET" in parallel
    for required in (
        "source_result",
        "transferable_primitive",
        "adaptation_hypothesis",
        "algorithm_candidate",
        "subdirection_split",
        "cross_direction_inspiration",
    ):
        assert required in reference


def test_adaptive_question_dispatch_is_bounded_advisory_and_order_invariant() -> None:
    """Cover adaptive routing as prose contracts, without creating a scheduler."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    role_normalized = " ".join(role.split())
    skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    skill_normalized = " ".join(skill.split())
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    parallel_normalized = " ".join(parallel.split())
    validation_contract = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    validation_normalized = " ".join(validation_contract.split())
    workflow_map = (REPO / "docs" / "project" / "WORKFLOW_MAP.md").read_text(
        encoding="utf-8"
    )
    workflow_map_normalized = " ".join(workflow_map.split())

    for required in (
        "adaptive_question_dispatch=bounded_registered_child_consultation",
        "adaptive_question_barrier=none_for_singleton|exact_named_question_set_only_when_joint",
        "adaptive_question_result_effect=consultation_only",
        "one clear, bounded, decision-relevant question",
        "expected information gain exceeds dispatch and synthesis cost",
        "no code, runtime, write, technical acceptance or formal scientific acceptance",
        "If evidence is sufficient and the next step is cheap and reversible, Explorer L1 decides directly.",
        "The child result is consultation only",
        "assigned Explorer remains the sole semantic local-research intake",
        "completion order is not evidence priority",
        "disagreement is not voting",
        "sole recovery is one low-cost retry with the identical question and source boundary",
        "These adaptive consultations do not alter the campaign phase barriers or the existing External Pro triggers.",
    ):
        assert required in role_normalized

    for required in (
        "Adaptive scientific question dispatch (not a fourth research mode)",
        "matching registered read-only research child",
        "Route source or metric fidelity to",
        "constructive mechanism analysis",
        "alternative/confound/falsifier analysis",
        "causal-hypothesis, repair or discriminator design",
        "When evidence is sufficient and the next step is cheap and reversible, Explorer decides directly.",
        "not a fourth research mode or an automatic pipeline",
        "A child answer is advisory input to one Explorer decision",
        "Canonical campaign rosters, ordered barriers and single-writer authority remain unchanged.",
        "best-matching registered read-only research child",
        "For the direction, the compact continuity projection contains the direction pointer, exact dependency, compact returned conclusion and CPM readiness.",
        "A cross-direction implication is represented only by a compact named edge sent EM→Root",
        "accepted CPM result may first go to one direction-specific read-only child",
    ):
        assert required in skill_normalized

    for required in (
        "singleton adaptive question creates no global barrier",
        "exact joint roster has a local merge barrier only when every named answer is a necessary input",
        "adaptive_first_round_peer_reading=forbidden",
        "persistent_explorer_progress=forbidden",
        "First-round assignments do not read peers or a favored answer",
        "Preserve disagreements as advisory inputs; never vote or collapse them into a quorum.",
        "There is no fixed adaptive count, concurrency, quorum, every-B panel, automatic-Pro path or durable mechanism.",
        "Explorer L1 remains the semantic author and integrates answers into one exact advisory decision; Research Artifact Writer and Root perform only the bounded physical writes described above.",
    ):
        assert required in parallel_normalized

    for stale in (
        "heartbeat",
        "timed wake",
        "deadline stop",
        "at-most-one-new-treatment-per-turn",
        "one-new-treatment-per-heartbeat",
        "per-heartbeat",
    ):
        assert stale not in " ".join((role_normalized, skill_normalized, parallel_normalized)).lower()

    child_roles = {
        "scout": (REPO / ".agents" / "roles" / "RESEARCH_SCOUT.md").read_text(
            encoding="utf-8"
        ),
        "innovator": (REPO / ".agents" / "roles" / "RESEARCH_INNOVATOR.md").read_text(
            encoding="utf-8"
        ),
        "principles": (
            REPO / ".agents" / "roles" / "RESEARCH_PRINCIPLES_ANALYST.md"
        ).read_text(encoding="utf-8"),
        "critic": (REPO / ".agents" / "roles" / "RESEARCH_CRITIC.md").read_text(
            encoding="utf-8"
        ),
    }
    child_expectations = {
        "scout": (
            "candidate_validation_scope=exact_source_terminology_metric_citation_counterevidence_or_evidence_boundary_fidelity",
        ),
        "innovator": (
            "candidate_validation_capabilities=causal_hypothesis_construction|candidate_repair|separating_prediction|smallest_next_discriminator|outcome_pattern_decision_map|mechanism_simplification",
            "cannot recheck acceptance, start or schedule an experiment",
        ),
        "principles": (
            "review_nature=constructive_not_adversarial",
            "without redoing technical acceptance or promoting a formal direction",
        ),
        "critic": (
            "criticism_modes=canonical_campaign|adaptive_bounded",
            "Only canonical campaign criticism requires that terminal",
            "Adaptive bounded criticism has no campaign-barrier effect",
        ),
    }
    for name, required_terms in child_expectations.items():
        child_normalized = " ".join(child_roles[name].split())
        for required in required_terms:
            assert required in child_normalized

    for required in (
        "project-validation",
        "direction-local",
        "scientific",
        "External Pro",
    ):
        assert required in " ".join((role_normalized, skill_normalized, validation_normalized))
    assert "research_treatment_pro_trigger=direction_changing_or_material_ambiguity_or_final_alignment_or_conclusion_or_explicit_C_review_or_explicit_user_request" in role
    assert "direction-local context binding" in workflow_map_normalized
    assert "Research and CPM operational dependency details remain in their owner contracts" in workflow_map_normalized
    for retired in (
        "resource_consuming_experiment_action=one_at_a_time_for_attribution",
        "Explorer names at most one resource-consuming experiment action at a time",
        "one resource-consuming experiment action active",
        "one isolated candidate at a time",
        "one-candidate-at-a-time",
        "queued_capacity_state=",
        "Insufficient capacity is `queued`",
        "global_serial_fallback=allowed",
        "global_serial_fallback=default",
        "global_serial_fallback=serial_by_default",
        "attribution requires serialization",
        "completion order determines dispatch",
    ):
        assert retired not in role + parallel + validation_contract


def test_parallel_first_normal_path_rejects_attribution_lock_regression() -> None:
    """Independent ready treatments cannot silently regain a global lock."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    parallel = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    exploration_skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    validation_skill = (
        REPO / ".agents" / "skills" / "hmasd-explorer-project-validation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    validation_contract = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    handoffs = (REPO / "docs" / "project" / "handoffs" / "README.md").read_text(
        encoding="utf-8"
    )
    principles = (REPO / "docs" / "project" / "ALGORITHM_PRINCIPLES.md").read_text(
        encoding="utf-8"
    )

    role_normalized = " ".join(role.split())
    parallel_normalized = " ".join(parallel.split())
    surfaces = (role, parallel, exploration_skill, validation_skill, validation_contract, handoffs)
    for required in (
        "parallel_dispatch=independent-ready-treatments-when-no-known-conflict",
        "serialization=exact-dependency-or-known-resource-or-mutable-path-conflict-only",
    ):
        assert required in parallel_normalized
    for required in (
        "parallel dispatch",
        "known conflict",
        "exact dependency",
        "mutable-path",
        "task tree",
        "event-driven",
        "Root-resumed",
    ):
        assert any(required.lower() in " ".join(surface.split()).lower() for surface in surfaces)

    # The old producer sentence would reintroduce a global attribution lock.
    section_three = principles.split("## 4. Evidence Design", 1)[0]
    assert "Schedule one resource-consuming action at a time for attribution" not in section_three
    for stale in (
        "one resource-consuming action at a time for attribution",
        "global serial lock by default",
        "serialize independent treatments for attribution",
        "current sole action permits serialization",
    ):
        normalized_surfaces = " ".join(" ".join(surface.lower().split()) for surface in surfaces)
        assert stale.lower() not in normalized_surfaces


def test_runtime_requests_are_explicit_and_have_no_fixed_admission_model() -> None:
    """Runtime work is a Root-routed natural-language request, not a pool gate."""
    surfaces = [
        (REPO / "AGENTS.md").read_text(encoding="utf-8"),
        (REPO / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md").read_text(
            encoding="utf-8"
        ),
        (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
            encoding="utf-8"
        ),
        (REPO / ".agents" / "skills" / "hmasd-agile-research-development" / "SKILL.md").read_text(
            encoding="utf-8"
        ),
        (
            REPO
            / ".agents"
            / "skills"
            / "hmasd-explorer-project-validation"
            / "SKILL.md"
        ).read_text(encoding="utf-8"),
        (
            REPO
            / ".agents"
            / "skills"
            / "hmasd-independent-research-exploration"
            / "references"
            / "parallel-research-workflow.md"
        ).read_text(encoding="utf-8"),
        (REPO / "docs" / "project" / "WORKFLOW_MAP.md").read_text(encoding="utf-8"),
    ]
    normalized = " ".join(" ".join(surface.split()) for surface in surfaces).lower()

    for required in (
        "runtime request",
        "natural-language",
        "requested-action",
        "required-resource",
        "known-conflict",
        "root-confirmed-user-authorization",
        "root",
        "cpm",
    ):
        assert required in normalized, required

    # The former pool/class/unit vocabulary must not remain an active contract.
    for stale in (
        "runtime_concurrency=three_unit_cpm_capacity_pool",
        "runtime_capacity_units_total=3",
        "runtime_capacity_admission_owner=code_project_manager",
        "runtime_admission_judgment=admit|up-class|pending_runtime_capacity",
        "B_TOY_LIGHT:1|B_TOY_MEDIUM:2|B_HEAVY_OR_C:3_exclusive",
        "three independent light treatments, or one medium plus one light",
        "sum the units of currently active result-bearing treatments",
        "experiment_pool_exclusive_runtime",
        "reservation/ledger",
        "hash admission",
    ):
        assert stale.lower() not in normalized, stale

    # CPM is a Root sibling and does not become a child of Explorer.
    router = surfaces[0].lower()
    assert "code_project_manager_parent=root" in router
    assert "independent_research_explorer_parent=root" in router
    assert "cpm" in router and "explorer" in router


def test_explorer_workflow_authority_is_centralized_and_transport_is_delegated() -> None:
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    retired_transport_profile_path = REPO / ".codex" / "agents" / "hmasd-agentify-transport.toml"
    assert not retired_transport_profile_path.exists()
    transport_profile_path = REPO / ".codex" / "agents" / "hmasd-explorer-agentify-transport.toml"
    assert transport_profile_path.is_file()
    transport_profile = transport_profile_path.read_text(encoding="utf-8")
    transport_role_path = REPO / ".agents" / "roles" / "EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md"
    assert transport_role_path.is_file()
    transport_role = transport_role_path.read_text(encoding="utf-8")
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
        "workflow_change_request_route=Root_to_workflow_design_manager",
        "git_authority=none",
        "current_work_read=read_only_as_needed_for_named_assignment",
        "local_research_write_tool=delegated_L2_or_root_proposal",
        "local_research_shell_mutation=forbidden",
        "continuity_entry=assignment_named_scope_compact_continuity_pointer",
        "continuity_owner=assigned_explorer_l1_task",
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
        "cross_task_transport=return_to_root",
        "cross_owner_route=explorer_to_root_to_cpm_or_reverse",
        "cross_task_target=root_task_context",
        "cross_task_model_and_thinking_overrides=omit",
        "independent_pro_review_assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:",
        "independent_pro_review_item_root=local_research/pro_reviews/<review-id>/",
        "independent_pro_review_request_and_intake_authority=exclusive_for_explorer_direction_and_methodology_reviews",
        "agentify_transport_child=hmasd-explorer-agentify-transport",
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
    for required in (
        "callable_agent_type=hmasd-explorer-agentify-transport",
        "parent=independent_research_explorer",
        "requester_partition_root=temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/",
        "output_contract=conclusion_first_return_to_parent",
        "write_authority=assignment_exact_transport_paths_only",
    ):
        assert required in transport_role
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
        "Return one exact requirement or defect to Root for relay to the current Workflow Design Manager task",
        "never load the collaborative/audit Workflow Skills",
        "no archived task ID, manager-session registry or route registry is required",
        "A direction scope does not scan for global continuity merely because it is absent",
    ):
        assert required in skill_normalized
    for required in (
        "one minimal JSON batch retaining the existing",
        "AGENTIFY_REVIEW_BATCH_RESULT",
        "registered `hmasd-explorer-agentify-transport` child",
        "AGENTIFY_REVIEW_BATCH_ASSIGNMENT",
        "batch_path|results_path",
        "silent while live",
        "exactly once through its native final response",
        "status|results_path|error",
        "terminal status `COMPLETE|ERROR`",
        "no polling, progress handling or parent-task result relay",
    ):
        assert required in pro_review_skill_normalized
    assert "$hmasd-collaborative-workflow-design" not in skill
    assert "$hmasd-workflow-change-audit" not in skill

    for required in (
        "This Skill is invoked only by the task-scoped Root-owned `INDEPENDENT_RESEARCH_EXPLORER` L1.",
        "there is no separate review-operator task or manager-session continuity.",
        "dispatch one self-contained",
        "`AGENTIFY_REVIEW_BATCH_ASSIGNMENT`",
        "registered `hmasd-explorer-agentify-transport` child",
        "batch_path|results_path",
        "silent while live",
        "exactly once through its native final response",
        "status|results_path|error",
        "terminal status `COMPLETE|ERROR`",
        "no polling, progress handling or parent-task result relay",
        "copy each named successful raw response",
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
        'name = "hmasd-explorer-agentify-transport"',
        'model = "gpt-5.6-luna"',
        'model_reasoning_effort = "medium"',
        "parent=independent_research_explorer",
        "temp/sessions/agentify_transport_operator/independent_research_explorer/<assignment>/",
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
        "scope_startup=exact_assignment_and_named_pointers",
        "direction_global_continuity=not_implicitly_loaded",
        "direction_scope_grammar=id=[a-z0-9][a-z0-9._-]{0,63}|no_path_separators|no_extra_colon|no_whitespace|nonempty|not_..",
        "continuity_entry=local_research/RESEARCH_CONTINUITY.md",
    ):
        assert required in parallel_normalized

    for required in (
        "path_role=independent_research_explorer",
        "startup_scope=fresh_cli_root_task|exact_assignment",
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

    for required in (
        "project_validation_intake_boundary=scientific_only_after_cpm_technical_acceptance",
        "project_validation_technical_recompute=forbidden_unless_scientifically_ambiguous",
        "project_validation_semantic_acceptance_owner=external_pro",
        "reverse_intake_scope=direction_only_delta",
        "direction-only reverse-intake",
        "project-validation scientific intake",
    ):
        assert required in role or required in exploration_skill, required

    pointer = "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    for surface in (role, validation_skill, exploration_skill, parallel, handoffs):
        assert pointer in surface, "scientific-only intake surface must point to its single source"

    assert "project_validation_intake_boundary=scientific_only_after_cpm_technical_acceptance" in role
    assert "project_validation_technical_recompute=forbidden_unless_scientifically_ambiguous" in role
    assert "canonical_scientific_decision_record=one_per_candidate_under_existing_local_research_ownership|advisory_only_not_formal_project_science" in role
    assert "root_macro_science=advisory_cross_direction_comparison|ranking|pause_continue|dependency_combination_decisions|complete_direction_action_map_acceptance" in role
    assert "External Pro" in contract


def test_direction_local_context_binding_is_symmetric_and_preserves_artifacts() -> None:
    role = " ".join(
        (REPO / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md")
        .read_text(encoding="utf-8")
        .split()
    )
    skill = " ".join(
        (REPO / ".agents/skills/hmasd-independent-research-exploration/SKILL.md")
        .read_text(encoding="utf-8")
        .split()
    )
    parallel = " ".join(
        (
            REPO
            / ".agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )

    for surface in (role, skill, parallel):
        assert "direction:<id>" in surface
        assert "research_scope_key" in surface
        assert "direction-local" in surface
        assert "Root" in surface
        assert "project-validation" in surface
    assert "portfolio_scope=" not in role
    assert "portfolio_scope=" not in skill
    assert "portfolio_scope=" not in parallel
    assert "direction-only" in role
    assert "external-review request/intake" in role
    assert "compact named edge" in skill
    assert "EM→Root" in parallel
    assert "never_sibling_comparison" in parallel


def test_explorer_mechanical_child_is_context_isolated_from_science() -> None:
    """The mechanical lane organizes literals without joining research rosters."""
    role_path = REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md"
    skill_path = REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    mechanical_role_path = REPO / ".agents" / "roles" / "EXPLORER_MECHANICAL_OPERATOR.md"
    mechanical_skill_path = REPO / ".agents" / "skills" / "hmasd-explorer-mechanical" / "SKILL.md"
    parallel_path = (
        REPO
        / ".agents"
        / "skills"
        / "hmasd-independent-research-exploration"
        / "references"
        / "parallel-research-workflow.md"
    )
    profile_path = REPO / ".codex" / "agents" / "hmasd-explorer-mechanical.toml"
    assert profile_path.is_file()

    role = " ".join(role_path.read_text(encoding="utf-8").split())
    skill = " ".join(skill_path.read_text(encoding="utf-8").split())
    mechanical_role = " ".join(mechanical_role_path.read_text(encoding="utf-8").split())
    mechanical_skill = " ".join(mechanical_skill_path.read_text(encoding="utf-8").split())
    parallel = " ".join(parallel_path.read_text(encoding="utf-8").split())
    assert "hmasd-explorer-mechanical" in role
    assert "hmasd-explorer-mechanical" in skill

    for required in (
        "explorer_mechanical_child=hmasd-explorer-mechanical",
        "explorer_mechanical_parent=independent_research_explorer",
        "explorer_mechanical_dispatch_order=direct_deterministic_commands|existing_exact_script|mechanical_child",
        "explorer_mechanical_task=literal_fact_organization_only",
        "explorer_mechanical_write_authority=none",
        "explorer_mechanical_scientific_authority=none",
        "explorer_mechanical_research_state_effect=none",
    ):
        assert required in role.lower()
    for required in (
        "heterogeneous record handling out of its scientific context",
        "literal existence or inaccessibility",
        "does not judge locator validity",
    ):
        assert required in mechanical_role.lower()
    for required in (
        "hmasd-explorer-mechanical",
        "exact deterministic read-only script",
        "read-only",
        "self-contained",
        "do not add a custom script in this route",
        "not a cheap scientific consultant",
        "while keeping scientific purpose, interpretation and next-action decisions with the explorer",
    ):
        assert required in mechanical_skill.lower()
    for required in (
        "explorer_mechanical_child=hmasd-explorer-mechanical",
        "explorer_mechanical_scientific_effect=none",
    ):
        assert required in parallel.lower()


def test_action_bearing_minimum_rejects_status_only_handoffs() -> None:
    """Direction EM/CM handoffs retain complete action-bearing semantics."""
    contract = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(contract.split())
    for required in (
        "direction-scoped advisory Independent Research Explorer (EM)",
        "Code Project Manager (CM) slice",
        "research_scope_key=direction:<id>",
        "EM direction:<id> -> Root -> CM direction:<id>",
        "## Strong action-bearing semantic minimum",
        "Every EM brief, CM result and Codex-native fallback",
        "conclusion-first action brief",
        "current evidence and exact paths",
        "facts and choices are frozen",
        "facts or choices remain unfrozen",
        "why CM is needed now",
        "why EM is needed now",
        "exact owner and the permitted action now",
        "evidence that will demonstrate completion",
        "return destination and the scientific/intake boundary",
        "Status-only text is insufficient",
        "waiting for CM",
        "CODE_ACCEPTED",
        "does not infer an action from a token",
    ):
        assert required.lower() in normalized.lower(), required


def test_parked_pending_and_retired_are_distinct_scientific_dispositions() -> None:
    role = (REPO / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    skill = (REPO / ".agents/skills/hmasd-independent-research-exploration/SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join((role + skill).split())
    for required in (
        "direction-local",
        "park-retire decision",
        "Root's advisory macro pause/continue boundary",
        "project-canonical science",
        "external-review request/intake",
    ):
        assert required in normalized, required
    assert "portfolio_scope=" not in normalized


def test_direction_action_map_is_exact_and_non_authoritative() -> None:
    role = " ".join(
        (REPO / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md")
        .read_text(encoding="utf-8")
        .split()
    )
    parallel = " ".join(
        (
            REPO
            / ".agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md"
        )
        .read_text(encoding="utf-8")
        .split()
    )
    for required in (
        "complete Direction Action Map acceptance",
        "direction-only delta",
        "root_direction_action_map_acceptance=complete_map|cross_direction_relations|unselected_rows|table_map|portfolio_continuity_after_affected_direction_input",
        "Root then checks the exact path and Git revision locator before exact-copy installation",
        "Explorer then full-reads the candidate's own `direction:<id>` row/delta and semantically accepts or rejects only that direction-local meaning",
        "Root owns acceptance of the complete Direction Action Map and cross-direction relations",
        "compact named edge",
        "EM→Root",
    ):
        assert required in role or required in parallel, required
    assert "Explorer L1 is the semantic author of a small, self-contained direction-only delta" in role
    assert "Root owns acceptance of the complete Direction Action Map" in role


def test_explorer_scope_tasks_preserve_direction_and_portfolio_context_boundaries() -> None:
    """Real Explorer tasks are one-direction scopes with Root macro authority."""
    role = (REPO / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    profile = (REPO / ".codex/agents/hmasd-independent-research-explorer.toml").read_text(
        encoding="utf-8"
    )
    skill = (REPO / ".agents/skills/hmasd-independent-research-exploration/SKILL.md").read_text(
        encoding="utf-8"
    )
    reference = (
        REPO
        / ".agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md"
    ).read_text(encoding="utf-8")
    surfaces = tuple(" ".join(text.split()) for text in (role, profile, skill, reference))
    combined = " ".join(surfaces)

    for required in (
        "research_scope_key_forms=direction:<id>",
        "direction_scope_grammar=id=[a-z0-9][a-z0-9._-]{0,63}",
        "direction_scope_owner=one_direction_scientific_meaning_only",
        "root_macro_science=advisory_cross_direction_comparison|ranking|pause_continue|dependency_combination_decisions|complete_direction_action_map_acceptance",
        "Read-only Sol-max L1 manager for one Root-created Explorer direction.",
        "one `direction:<id>` Explorer direction",
        "There is no portfolio Explorer scope.",
        "does not preload the whole portfolio",
        "compact named edge",
        "EM→Root",
    ):
        assert required in combined, required
    assert "portfolio_scope=" not in role
    assert "portfolio_scope=" not in skill
    assert "portfolio_scope=" not in reference
    assert "Root does not execute direction research" in combined


def test_explorer_instances_are_scope_keyed_and_not_root_singletons() -> None:
    """Explorer L1 multiplicity follows distinct research scope keys."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    assert "multiple_scoped_instances_per_root_tree=true" in role
    assert "one_instance_per_owner_per_root_tree=true" not in role


def test_scope_transport_and_worktree_ownership_stay_root_routed() -> None:
    """Scope bindings survive relay while lifecycle and Git stay with Root."""
    surfaces = (
        (REPO / "AGENTS.md").read_text(encoding="utf-8"),
        (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
            encoding="utf-8"
        ),
        (REPO / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md").read_text(
            encoding="utf-8"
        ),
        (
            REPO
            / "docs"
            / "project"
            / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
        ).read_text(encoding="utf-8"),
        (
            REPO
            / ".agents"
            / "skills"
            / "hmasd-independent-research-exploration"
            / "references"
            / "parallel-research-workflow.md"
        ).read_text(encoding="utf-8"),
    )
    normalized = " ".join(" ".join(surface.split()) for surface in surfaces).lower()

    for required in (
        "explorer",
        "root",
        "cpm",
        "research_scope_key",
        "direction",
        "candidate",
        "revision",
        "explorer_to_root_to_cpm",
        "reverse",
        "one-root-managed-worktree-per-writable-l1",
        "all-exact-disjoint-writers-share-the-scope-worktree",
        "l2_workspace_lifecycle=none",
        "l2_helper_authority=none",
        "git_authority=none",
    ):
        assert required in normalized, required

    assert "cpm remains a root sibling" in normalized or (
        "code_project_manager_parent=root" in normalized
        and "independent_research_explorer_parent=root" in normalized
    )
    assert "never_nested_under_explorer" in normalized
    assert "explorer -> cpm" not in normalized


def test_explorer_orchestrates_direction_and_routes_macro_findings_to_root() -> None:
    """Direction Explorer owns local science; Root owns macro comparison."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    skill = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-exploration" / "SKILL.md"
    ).read_text(encoding="utf-8")
    role_normalized = " ".join(role.split())
    skill_normalized = " ".join(skill.split())

    for surface in (role_normalized, skill_normalized):
        assert "root retains only" not in surface.lower()
        assert "root explorer retains only" not in surface.lower()

    for required in (
        "explorer_orchestration_owner=direction_local_decomposition|child_selection|dependency_judgment|result_synthesis|scope_continuity|project_validation_intake|external_review_intake|direction_only_reverse_intake",
        "direction_state_retention=direction_pointer|dependency|compact_returned_conclusion|cpm_readiness|named_cross_direction_findings",
        "direction_cross_direction_reporting=compact_named_findings_to_root_only",
        "child_direction_context=minimal_direction_context_only|never_hidden_parent_context|no_sibling_direction_loading_or_comparison",
        "direction-local scientific/advisory intake",
        "user-authorized, advisory macro/portfolio science",
        "complete Direction Action Map acceptance",
        "compact named edge",
        "EM→Root",
        "never sibling loading, comparison, ranking or selection",
        "project_validation_semantic_acceptance_owner=external_pro",
        "project_validation_alignment_packet_effect=authoritative_scientific_semantic_acceptance",
    ):
        assert required in role_normalized or required in skill_normalized, required

    # Outstanding child/CPM work cannot block safe read-only progress, but a
    # bounded wait is allowed for a true direction-local dependency.
    for required in (
        "explorer_l1_nonblocking_progress=advance_disjoint_direction_local_actions_and_read_only_work_while_child_or_cpm_result_outstanding",
        "explorer_l1_bounded_wait=only_when_every_remaining_safe_scientific_action_depends_on_outstanding_result",
        "While one child or CPM result is outstanding, continue every other disjoint read-only or direction-local scientific action.",
        "Use a bounded wait only when every remaining safe scientific action depends on that outstanding result",
    ):
        assert required in role_normalized or required in skill_normalized, required

    # Cheap reversible singleton reasoning and direction-local intake stay
    # direct; macro authority and the protected postcondition remain with Root.
    for required in (
        "direct_explorer_l1_work_exceptions=cheap_reversible_singleton|advisory_local_research_intake|frozen_successor|park_or_retire_decision",
        "Direct Explorer-L1 work remains appropriate for a cheap reversible singleton",
        "Every child return is conclusion-first and action-bearing enough for synthesis",
        "Explorer L1 verifies the protected scientific postcondition before advisory local-research intake",
        "root_macro_pause_continue=advisory_root_decision",
        "canonical_scientific_authority=none",
        "Do not microdelegate",
        "fixed panel",
        "scientific-authority transfer",
    ):
        assert required in role_normalized or required in skill_normalized, required


def test_reverse_intake_is_small_file_backed_and_keeps_science_with_explorer() -> None:
    explorer_role = (REPO / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    combined = " ".join(explorer_role.split())

    for required in (
        "reverse_intake_payload=small_self_contained_semantic_delta",
        "reverse_intake_required_bindings=canonical_source_locator|candidate_target_locator|git_revision_locator|exact_old_new_text_or_unified_patch|frozen_semantics_and_consequences",
        "reverse_intake_transport=assignment_specific_temporary_patch",
        "reverse_intake_explorer_acceptance=full_read_own_direction_row_delta_semantic_accept_or_reject",
        "root_direction_action_map_acceptance=complete_map|cross_direction_relations|unselected_rows|table_map|portfolio_continuity_after_affected_direction_input",
        "The full map never travels through an agent message",
        "exact old/new text or a unified patch",
        "Explorer then full-reads the candidate's own `direction:<id>` row/delta and semantically accepts or rejects only that direction-local meaning",
        "Explorer does not accept archive or locator meaning, unselected rows, table/map meaning or portfolio continuity outside its own row/delta",
        "Root owns acceptance of the complete Direction Action Map and cross-direction relations",
        "assignment_specific_reverse_intake_patch",
        "research_artifact_writer_continuity_write=forbidden",
        "scientific_authority=none",
        "reverse_intake_semantic_author=independent_research_explorer",
        "Root owns acceptance of the complete Direction Action Map",
        "direction-only reverse-intake",
    ):
        assert required.lower() in combined.lower(), required

    assert "scripts/hmasd_state_transform.py" not in combined
    assert "source_sha256=" not in combined
    assert "candidate_sha256=" not in combined
