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
        "adaptive_question_barrier=none_for_singleton|exact_local_roster_only_when_joint",
        "adaptive_question_result_effect=consultation_only",
        "owner_task_scheduler=same_level_user_owned_Desktop_Explorer_task",
        "owner_mode=direction|portfolio",
        "owner_task_assignment=self_contained_natural_language",
        "owner_task_exact_inputs=canonical_inputs_named_by_assignment",
        "owner_task_write_paths=canonical_write_paths_named_by_assignment",
        "owner_task_result_destination=canonical_result_destination_named_by_assignment",
        "owner_task_result=conclusion_first_canonical_capsule",
        "resource_model=observed_resource_vector_and_conflict_set",
        "resource_vector_dimensions=cpu|memory|gpu|process|io|network|paid_service|mutable_path|mutable_object|output_root",
        "resource_observation_owner=scheduler_observes_actual_vectors_and_conflicts",
        "resource_admission_owner=code_project_manager_runtime_authority",
        "resource_conflict_serialization=only_named_dependency_or_observed_vector_or_mutable_conflict",
        "active_experiment_roster_owner=independent_research_explorer_scientific_view",
        "independent_ready_treatment_dispatch=parallel_first_when_vectors_are_disjoint",
        "global_serial_fallback=forbidden_without_named_dependency_or_observed_conflict",
        "per_direction_result_bearing_default=one_active",
        "same_direction_parallelism=exact_frozen_joint_roster_only",
        "formal_local_runtime_exclusivity=explicit_formal_result_bearing_local_runtime_only",
        "formal_local_runtime_scope=conflicting_local_experiment_runtime_only",
        "formal_local_runtime_nonblocking=research|intake|code|review|Pro|unrelated_nonruntime",
        "resource_wait_effect=pending_observed_resource_conflict_only_nonruntime_continues",
        "evidence_level_runtime_orthogonal=true",
        "No resource condition blocks research, result intake, read-only analysis, Pro review or another non-runtime action.",
        "one clear, bounded, decision-relevant question",
        "expected information gain exceeds dispatch and synthesis cost",
        "no code, runtime, write, technical acceptance or formal scientific acceptance",
        "If evidence is sufficient and the next step is cheap and reversible, Explorer decides directly.",
        "The child result is consultation only",
        "Explorer remains the portfolio integrator and writes exactly one canonical scientific decision",
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
    ):
        assert required in skill_normalized

    for required in (
        "adaptive_question_roster=singleton_or_exact_joint_roster",
        "adaptive_singleton_global_barrier=none",
        "adaptive_joint_local_merge_barrier=only_when_every_named_answer_is_necessary",
        "adaptive_first_round_peer_reading=forbidden",
        "First-round assignments do not read peers or a favored answer",
        "Preserve disagreements as advisory inputs; never vote or collapse them into a quorum.",
        "There is no fixed adaptive count, concurrency, quorum, every-B panel or automatic-Pro path.",
        "The Explorer remains the single writer and integrates answers into one decision.",
        "resource_model=observed_resource_vector_and_conflict_set",
        "resource_vector_dimensions=cpu|memory|gpu|process|io|network|paid_service|mutable_path|mutable_object|output_root",
        "Resource waits leave research, intake, code, review, Pro and other non-runtime owner tasks runnable",
        "Every concurrent treatment has distinct direction/treatment identity, canonical design, CPM ticket/worktree, source freeze and accepted commit, run, evidence, checkpoint and result roots, seed/RNG namespace, temporary session paths, Operator receipt, readiness/technical-acceptance record and Explorer decision",
        "By default a direction has at most one result-bearing treatment active",
        "successor waits until the predecessor is terminal and Explorer completes that direction's scientific intake",
        "Explorer freezes one exact joint roster before any member starts",
        "Completion order is never scientific priority, voting or a cross-direction barrier",
        "Scheduler owner-task lifecycle events replace polling or background scheduling",
        "Strict methodology is scoped to conclusion-bearing C work or a named science-review trigger, not all candidate validation.",
        "normal path for two or more scientifically selected and frozen independent treatments is parallel-first",
        "Attribution, generic caution, completion order and convenience are not resource evidence",
    ):
        assert required in parallel_normalized

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
        "does not recompute schema, readability, receipts, activity counts, locators",
        "necessary to one Explorer decision",
        "Several read-only questions may run in parallel",
        "a direction keeps at most one result-bearing treatment active by default",
        "Independent ordinary A/B treatments from different directions may overlap",
        "exactly one CPM technical acceptance and one Explorer scientific intake",
        "ordinary B remains B and does not automatically invoke Pro",
        "consumes no formal iteration",
    ):
        assert required in validation_normalized
    assert "research_treatment_pro_trigger=direction_changing_or_material_ambiguity_or_final_alignment_or_conclusion_or_explicit_C_review_or_explicit_user_request" in role
    assert "direction-local context binding" in workflow_map_normalized
    assert "Research and CPM operational dependency details remain in their owner contracts" in workflow_map_normalized
    for retired in (
        "resource_consuming_experiment_action=one_at_a_time_for_attribution",
        "Explorer names at most one resource-consuming experiment action at a time",
        "one resource-consuming experiment action active",
        "one isolated candidate at a time",
        "one-candidate-at-a-time",
        "runtime_concurrency=three_unit_cpm_capacity_pool",
        "runtime_capacity_units_total=3",
        "runtime_capacity_classes=",
        "three-unit CPM runtime pool",
        "heartbeat",
        "persistent Explorer",
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
        "independent_ready_treatment_dispatch=parallel_first_when_vectors_are_disjoint",
        "global_serial_fallback=forbidden_without_named_dependency_or_observed_conflict",
    ):
        assert required in role_normalized
        assert required in parallel_normalized
    for required in (
        "selected and frozen",
        "direction-local predecessor/intake barrier",
        "parallel-first",
        "same-direction rules",
        "observed resource-vector conflict",
        "formal local result-bearing runtime",
        "resource wait",
        "non-runtime work",
        "owner-task lifecycle",
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
        "heartbeat",
        "three-unit",
    ):
        normalized_surfaces = " ".join(" ".join(surface.lower().split()) for surface in surfaces)
        assert stale.lower() not in normalized_surfaces


def test_frozen_twelve_direction_portfolio_is_distinct_from_concurrency_window() -> None:
    """The reference owns the detailed portfolio procedure and the target is not a pool."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    skill = (
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
    role_normalized = " ".join(role.split())
    skill_normalized = " ".join(skill.split())
    parallel_normalized = " ".join(parallel.split())
    surfaces_normalized = " ".join((role_normalized, skill_normalized, parallel_normalized))
    for required in (
        "portfolio_direction_target=12",
        "direction_owner_write_scope=one_disjoint_direction_capsule_only",
        "direction_owner_shared_continuity_write=forbidden",
        "direction_owner_sibling_write=forbidden",
        "scheduler_scientific_authority=none",
        "wdm_cpm_scheduler_scientific_authority=none",
        "detailed capsule, intake, readiness, ordering, ceiling and shortfall procedure is defined once in",
        "references/parallel-research-workflow.md",
    ):
        assert required.lower() in role_normalized.lower() + skill_normalized.lower(), required

    # Detailed semantics live in the parallel reference, not Role/Skill copies.
    for required in (
        "portfolio_direction_target=12",
        "portfolio_target_counts=scientific_direction_identities_only",
        "portfolio_canonical_surfaces=direction_specific_canonical_capsules|local_research/RESEARCH_CONTINUITY.md",
        "portfolio_shortfall_policy=record_exact_ambiguity_or_shortfall_never_pad",
        "direction_owner_write_scope=one_disjoint_direction_capsule_only",
        "portfolio_integration_boundary=stable_portfolio_integration_boundary",
        "portfolio_intake=exact_direction_results",
        "portfolio_scientific_fields=identities|status|eligibility|priority|dependencies",
        "portfolio_ready_assignment=conclusion_first_self_contained_ready_next_owner_assignment",
        "portfolio_ready_assignment_fields=exact_inputs|write_paths|result_destinations|dependencies|resource_vectors",
        "research_scheduler_task_creation=alone_same_level_direction_owner_tasks",
        "initial_configured_concurrency_ceiling=3",
        "initial_ceiling_counts=active_same_level_direction_owner_tasks_only",
        "scheduler_launch_policy=at_most_ceiling_and_fewer_on_actual_write_or_resource_conflicts",
        "scheduler_ready_order=mechanically_preserve_explorer_ready_order",
        "scheduler_conflict_skip=may_pass_over_conflicting_ready_item_for_later_disjoint_item",
        "scheduler_forbidden_semantics=invent|fill_slots|reprioritize|merge|retire|select_directions",
        "direction_completion_successor_gate=exact_portfolio_intake_and_continuity_update_before_successor_ready",
        "portfolio_size_separate_from_active_concurrency_window=true",
        "active_concurrency_window=flexible_per_run_ceiling",
        "fixed_runtime_pool=forbidden",
        "exact ambiguity or shortfall",
        "never pad",
        "natural-language portfolio capsule/continuity decision, not a schema, queue or admission gate",
        "Scheduler's command procedure",
    ):
        assert required.lower() in parallel_normalized.lower(), required

    # The detailed keys/prose are intentionally not copied into Role or Skill.
    for detailed in (
        "portfolio_canonical_surfaces=",
        "portfolio_intake=exact_direction_results",
        "initial_configured_concurrency_ceiling=3",
        "scheduler_ready_order=",
        "direction_completion_successor_gate=",
        "portfolio size 12 is separate from active concurrency window 3",
    ):
        assert detailed.lower() not in (role_normalized + skill_normalized).lower(), detailed

    # Remove redundant aliases: one canonical target key only.
    for alias in (
        "portfolio_size=12",
        "portfolio_target_direction_count=12",
        "portfolio_direction_identity_count=12",
    ):
        assert alias.lower() not in surfaces_normalized.lower(), alias

    # Source assignments, candidates and opportunities never inflate the 12.
    for excluded in (
        "source assignments are directions",
        "candidate records are directions",
        "subdirection opportunities are directions",
        "three directions portfolio",
        "three-direction portfolio",
        "portfolio of three directions",
        "portfolio_size=3",
    ):
        assert excluded.lower() not in surfaces_normalized.lower(), excluded
    # The active window is explicitly three direction owner tasks, not 12.
    assert "initial configured concurrency ceiling is 3 active same-level direction owner tasks" in parallel_normalized.lower()
    assert "portfolio size 12 is separate from active concurrency window 3" in parallel_normalized.lower()


def test_desktop_owner_modes_are_isolated_and_children_keep_their_contracts() -> None:
    """Scheduler owner tasks carry explicit direction/portfolio scope only."""
    role = (REPO / ".agents" / "roles" / "INDEPENDENT_RESEARCH_EXPLORER.md").read_text(
        encoding="utf-8"
    )
    exploration = (
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
    validation = (
        REPO / "docs" / "project" / "EXPLORER_PROJECT_VALIDATION_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    handoffs = (REPO / "docs" / "project" / "handoffs" / "README.md").read_text(
        encoding="utf-8"
    )
    surfaces = (role, exploration, parallel, validation, handoffs)
    normalized = " ".join(" ".join(surface.split()) for surface in surfaces)
    parallel_normalized = " ".join(parallel.split())
    for required in (
        "same-level user-owned Desktop Explorer owner task",
        "owner_mode=direction",
        "owner_mode=portfolio",
        "one named direction",
        "explicitly named direction set",
        "self-contained natural-language",
        "exact canonical inputs",
        "write paths",
        "result destination",
        "conclusion-first canonical capsule",
        "resource vectors",
        "resource-vector conflict",
        "Evidence level A/B/C is orthogonal",
        "formal local result-bearing runtime",
        "non-runtime work",
        "selects and freezes already-valued work",
        "requests/routes that work through Research Scheduler",
        "Research Scheduler alone creates the same-level user-owned Desktop Explorer owner task",
        "never creates a new owner assignment",
        "Scheduler has no semantic authority",
        "local experiment-runtime admission",
    ):
        assert required.lower() in normalized.lower(), required
    for required in (
        "owner_assignment_write_scope=exact_direction_or_portfolio_files_or_strict_descendants_under_local_research|optional_one_strict_descendant_under_temp_handoffs/explorer_to_code_manager",
        "owner_assignment_root_write_forbidden=true",
        "active_owner_write_path_overlap=equal_or_ancestor_descendant_overlap_fails_closed",
        "active_owner_write_path_conflict=serialize_or_re_slice",
        "disjoint_owner_write_paths=parallel_first",
        "owner_write_scope_isolation=mutation_scope_only_not_science_scheduling_queue_or_schema",
    ):
        assert required in role
    for required in (
        "exact direction- or portfolio-owned files",
        "strict descendants under `local_research/`",
        "at most one exact strict descendant under `temp/handoffs/explorer_to_code_manager/`",
        "A root path never grants the whole root",
        "equal or ancestor/descendant-overlapping write paths fail closed",
        "must serialize or be re-sliced",
        "disjoint direction paths remain parallel-first",
        "mutation-scope isolation, not science scheduling, a queue or a new schema",
    ):
        assert required.lower() in normalized.lower(), required
    assert (
        "never preloads sibling" in normalized.lower()
        or "without_sibling_preload" in normalized.lower()
    )
    assert "Explorer calls the registered agent type" in parallel_normalized
    assert "self-contained natural-language assignment" in parallel_normalized

    for profile_name in (
        "hmasd-research-scout.toml",
        "hmasd-research-innovator.toml",
        "hmasd-research-principles-analyst.toml",
        "hmasd-research-critic.toml",
        "hmasd-explorer-mechanical.toml",
        "hmasd-agentify-transport.toml",
    ):
        profile = (REPO / ".codex" / "agents" / profile_name).read_text(encoding="utf-8")
        assert "owner_mode=" not in profile
        assert "same-level user-owned Desktop Explorer" not in profile

    for forbidden in (
        "runtime_concurrency=three_unit_cpm_capacity_pool",
        "runtime_capacity_units_total=3",
        "three-unit CPM runtime pool",
        "heartbeat",
        "persistent Explorer",
        "current sole action permits serialization",
        "experiment-pool admission",
    ):
        assert forbidden.lower() not in normalized.lower(), forbidden


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
    pro_review_agent_prompt = (
        REPO / ".agents" / "skills" / "hmasd-independent-research-pro-review" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    pro_role = (REPO / ".agents" / "roles" / "EXTERNAL_PRO.md").read_text(encoding="utf-8")
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
        "startup_identity=role|owner_assignment|canonical_inputs",
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
        "The prose-first assignment supplies the exact canonical inputs",
        "one bounded owned-path scan",
    ):
        assert required in skill_normalized
    for required in (
        "one minimal JSON batch retaining the existing",
        "AGENTIFY_REVIEW_BATCH_RESULT",
        "registered `hmasd-agentify-transport` child",
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
        "invoked only from an assignment-scoped same-level user-owned Desktop Explorer owner task",
        "there is no separate review-operator owner task",
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
    for required in (
        "assignment-scoped direction/portfolio owner",
        "exact review boundary",
        "owner_mode=direction|portfolio",
        "exact canonical inputs",
        "exact canonical write paths",
        "exact result destination",
    ):
        assert required.lower() in pro_review_skill_normalized.lower()
    assert "assignment-scoped same-level user-owned Desktop Explorer owner task" in pro_review_agent_prompt
    assert "hmasd-independent-research-pro" not in pro_review_skill.replace(
        "hmasd-independent-research-pro-review", ""
    )

    assert "IR_DIRECTION_REVIEW:" in pro_review_skill
    assert "IR_METHODOLOGY_REVIEW:" in pro_review_skill
    assert "local_research/pro_reviews/<review-id>/" in pro_review_skill
    assert "IR_UNSUPPORTED_REVIEW:" not in pro_review_skill
    pro_role_normalized = " ".join(pro_role.split())
    for required in (
        "review_owner_task=same_level_user_owned_Desktop_Explorer_owner",
        "review_owner_mode=direction|portfolio",
        "review_boundary=assignment_scoped_exact_direction_or_named_direction_set",
        "review_exact_inputs=canonical_inputs_named_by_assignment",
        "review_write_paths=canonical_write_paths_named_by_assignment",
        "review_result_destination=canonical_result_destination_named_by_assignment",
        "scheduled_resource_consuming_action_scope=assignment_named_only",
        "scheduled_resource_consuming_action_count=not_global_scheduler_field",
    ):
        assert required in pro_role_normalized
    for forbidden in ("persistent Explorer", "persistent conversation", "current resource-consuming action"):
        assert forbidden.lower() not in pro_role_normalized.lower()
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
        "restart_identity=owner_assignment|canonical_capsules|exact_result_destination",
        "continuity_entry=local_research/RESEARCH_CONTINUITY.md",
        "active_experiment_roster",
        "last completed phase or direction-local intake barrier",
        "unfinished assignment or review",
        "next scientific action",
        "current authorized source boundary",
        "Update it only when the active roster changes",
        "one bounded scan",
    ):
        assert required in parallel_normalized

    for required in (
        "owner_role=independent_research_explorer",
        "owner_task_source=research_scheduler",
        "owner_mode=direction|portfolio",
        "startup_identity=role|owner_assignment|canonical_inputs",
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

    assert pointer in explorer_role
    assert pointer in exploration_skill
    assert pointer in validation_skill_normalized
    assert "direction-specific Explorer" in cpm_role_normalized

    assert "explicitly multi-direction user question" in normalized_contract
    assert "never imports another direction" in normalized_contract
    assert "portfolio-wide meaning" in normalized_contract
    assert "A Codex-native message fallback carries the same binding" in handoffs
    assert "excluding unrequested siblings" in exploration_skill
    assert "preserve the original handoff/artifact" in validation_skill_normalized
    assert "direction-local context binding" in workflow_map
    assert "never reads `local_research/`" in cpm_role_normalized


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
        "explorer_mechanical_scientific_roster=excluded",
        "explorer_mechanical_barrier=none",
        "explorer_mechanical_peer_independence=not_applicable",
        "explorer_mechanical_evidence_role=literal_fact_organization_not_scientific_evidence",
        "explorer_mechanical_campaign_effect=none",
    ):
        assert required in parallel.lower()
