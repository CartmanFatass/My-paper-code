from tools.hmasd_control_plane.constraint_lint import lint_repository, lint_text


def test_unregistered_fixed_constraint_is_linted():
    findings = lint_text("The project has a fixed direction count cap of 16.", "x.md")
    assert any(item.kind == "DIRECTION_CAP" for item in findings)


def test_resource_selected_worker_is_not_linted():
    text = "worker_count = 4\nresource_preflight_ref = 'x'\nNR-WORKER-LIMIT-001"
    assert lint_text(text, "x.toml") == []


def test_internal_sha_handoff_is_linted():
    assert lint_text("Internal handoff requires SHA-256.", "x.md")


def test_repository_lint_scans_roles_and_skills(tmp_path):
    (tmp_path / "docs/project").mkdir(parents=True)
    (tmp_path / ".agents/roles").mkdir(parents=True)
    (tmp_path / ".agents/skills/example").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("", encoding="utf-8")
    (tmp_path / ".agents/roles/ROLE.md").write_text("The project has a fixed direction count cap of 9.", encoding="utf-8")
    (tmp_path / ".agents/skills/example/SKILL.md").write_text("Every run has a hard global worker limit of 3.", encoding="utf-8")
    findings = lint_repository(tmp_path)
    paths = {item.path.replace("\\", "/") for item in findings}
    assert any(path.endswith(".agents/roles/ROLE.md") for path in paths)
    assert any(path.endswith(".agents/skills/example/SKILL.md") for path in paths)


def test_explicit_anti_constraints_are_not_linted():
    samples = (
        "Legacy one-attempt/no-retry labels are factual only, not routing authority.",
        "It is no longer required to masquerade as a single fixed direction.",
        "Reviewers are optional; do not build a mandatory review chain.",
    )
    for sample in samples:
        assert lint_text(sample, "role.md") == []
