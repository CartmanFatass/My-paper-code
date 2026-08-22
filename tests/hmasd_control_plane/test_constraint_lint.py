from tools.hmasd_control_plane.constraint_lint import lint_repository, lint_text


def test_unregistered_fixed_constraint_is_linted():
    findings = lint_text("The project has a fixed direction count cap of 16.", "x.md")
    assert any(item.kind == "DIRECTION_CAP" for item in findings)


def test_resource_selected_worker_is_not_linted():
    text = "worker_count = 4\nresource_preflight_ref = 'x'\nNR-WORKER-LIMIT-001"
    assert lint_text(text, "x.toml") == []


def test_internal_sha_handoff_is_linted():
    assert lint_text("Internal handoff requires SHA-256.", "x.md")


def test_constraint_lint_scans_roles(tmp_path):
    path = tmp_path / ".agents/roles/EXAMPLE.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "Every worker count must be exactly 16.\n",
        encoding="utf-8",
    )
    findings = lint_repository(tmp_path)
    assert any(item.path.endswith("EXAMPLE.md") for item in findings)


def test_constraint_lint_scans_skills(tmp_path):
    path = tmp_path / ".agents/skills/example/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "All internal handoffs require SHA-256.\n",
        encoding="utf-8",
    )
    findings = lint_repository(tmp_path)
    assert any(item.kind == "HASH_HANDOFF" for item in findings)


def test_unrelated_requirement_id_does_not_authorize_constraint():
    findings = lint_text(
        "UR-EXEC-001 applies. Every recovery has exactly one attempt.",
        path=".agents/roles/EXAMPLE.md",
    )
    assert any(item.kind == "ONE_ATTEMPT" for item in findings)


def test_direction_negation_does_not_suppress_later_positive_constraint():
    findings = lint_text(
        "There is no fixed direction count cap. "
        "The project has a maximum direction count of 16."
    )
    assert any(item.kind == "DIRECTION_CAP" for item in findings)


def test_exact_operation_reference_does_not_suppress_later_one_attempt_rule():
    findings = lint_text(
        "Keep the exact operation identifier in the report. "
        "Every recovery has exactly one attempt."
    )
    assert any(item.kind == "ONE_ATTEMPT" for item in findings)


def test_worker_negation_does_not_suppress_later_positive_constraint():
    findings = lint_text(
        "No project-wide worker cap applies. "
        "Every worker count must be exactly 16."
    )
    assert any(item.kind == "WORKER_LIMIT" for item in findings)


def test_pure_negation_paragraphs_are_not_linted():
    assert lint_text("There is no fixed direction count cap.") == []
    assert lint_text("No project-wide worker cap applies.") == []
    assert lint_text("There is no fixed one-attempt rule.") == []


def test_same_new_markdown_row_is_an_exact_operation_retry_fence():
    text = (
        "| Recovery fence | Same: observe only; no retry. "
        "New: a distinct authorized operation. |"
    )
    assert lint_text(text) == []


def test_requirement_id_is_not_itself_a_constraint_match():
    assert lint_text('id = "NR-WORKER-LIMIT-001"') == []
