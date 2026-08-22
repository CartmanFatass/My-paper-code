from pathlib import Path

import pytest

from tools.hmasd_control_plane.requirements_registry import Requirement, load_requirements, render_requirements_markdown, validate_registry


ROOT = Path("docs/project/PROJECT_REQUIREMENTS.toml")


def test_registry_loads_and_renders_deterministically():
    requirements = load_requirements(ROOT)
    rendered = render_requirements_markdown(requirements)
    assert "ACTIVE NONREQUIREMENTS" in rendered
    assert rendered == render_requirements_markdown(requirements)


def test_duplicate_id_is_rejected(tmp_path):
    path = tmp_path / "requirements.toml"
    path.write_text('[[requirements]]\nid="X"\nkind="DEFAULT"\nstatus="ACTIVE"\nauthority="P0_USER"\nowner="x"\nscope=["x"]\nsummary="a"\nsource_ref="user:x"\nenforced_at=["x"]\ndoes_not_imply=["x"]\ndeviation_policy="NONE"\n\n[[requirements]]\nid="X"\nkind="DEFAULT"\nstatus="ACTIVE"\nauthority="P0_USER"\nowner="x"\nscope=["y"]\nsummary="b"\nsource_ref="user:x"\nenforced_at=["x"]\ndoes_not_imply=["x"]\ndeviation_policy="NONE"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_requirements(path)


def test_validator_catches_unknown_kind_missing_source_and_empty_nonimplication():
    item = Requirement("X", "NOPE", "ACTIVE", "P0_USER", "x", ("x",), "x", "local", ("x",), (), "NONE")
    errors = validate_registry({"X": item})
    assert any("unknown kind" in error for error in errors)
    assert any("P0 source" in error for error in errors)
    assert any("does_not_imply" in error for error in errors)
