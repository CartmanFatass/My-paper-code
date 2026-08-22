from tools.hmasd_control_plane.constraint_lint import lint_text


def test_unregistered_fixed_constraint_is_linted():
    findings = lint_text("The project has a fixed direction count cap of 16.", "x.md")
    assert any(item.kind == "DIRECTION_CAP" for item in findings)


def test_resource_selected_worker_is_not_linted():
    text = "worker_count = 4\nresource_preflight_ref = 'x'\nNR-WORKER-LIMIT-001"
    assert lint_text(text, "x.toml") == []


def test_internal_sha_handoff_is_linted():
    assert lint_text("Internal handoff requires SHA-256.", "x.md")
