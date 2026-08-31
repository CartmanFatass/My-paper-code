from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents" / "skills" / "hmasd-pro-research-prompt-author" / "scripts" / "render_packet.py"
SKILL = ROOT / ".agents" / "skills" / "hmasd-pro-research-prompt-author" / "SKILL.md"


def _renderer():
    spec = importlib.util.spec_from_file_location("hmasd_prompt_author_renderer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request() -> dict[str, object]:
    return {
        "caller_role": "em",
        "request_id": "req-companion-01",
        "direction_id": "demo_direction",
        "repository": "C:/repo",
        "repository_url": "https://github.com/example/repo",
        "commit_or_ref": "0123456789abcdef0123456789abcdef01234567",
        "scientific_question": "Does the bounded intervention change the stated endpoint?",
        "deliverable": "A conclusion-first evidence assessment.",
        "claim_ceiling": "Descriptive finite-panel claim only.",
        "reference_files": [
            {
                "path": "docs/research/candidates/demo_direction/DIRECTION.md",
                "purpose": "direction definition",
                "provenance": "registered direction authority",
            }
        ],
    }


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    direction = tmp_path / "docs" / "research" / "candidates" / "demo_direction"
    portfolio = tmp_path / "docs" / "research" / "portfolio"
    direction.mkdir(parents=True)
    portfolio.mkdir(parents=True)
    (direction / "DIRECTION.md").write_text("# Demo\n", encoding="utf-8")
    (portfolio / "PORTFOLIO.md").write_text("| demo_direction | ACTIVE |\n", encoding="utf-8")
    return tmp_path


def _render(renderer, request: dict[str, object], project_root: Path, out_dir: Path) -> dict:
    packet = renderer.validate(request, project_root)
    renderer.render(packet, out_dir)
    return json.loads((out_dir / "HANDOFF.json").read_text(encoding="utf-8"))


def test_omitted_companion_prompt_uses_the_fixed_default(project_root: Path, tmp_path: Path) -> None:
    renderer = _renderer()
    packet = renderer.validate(_request(), project_root)

    assert packet["companion_prompt"] == (
        "Execute the exact scientific research request in the attached PROMPT_BODY.md. "
        "Use the separately attached REFERENCE_FILES.md only as its read-only GitHub evidence manifest. "
        "The author remains authoring-only and must not send, open a browser, bind a conversation, "
        "or validate Transport state."
    )
    handoff = _render(renderer, _request(), project_root, tmp_path / "default")
    assert handoff["transport_request"]["companion_prompt"] == packet["companion_prompt"]


def test_non_empty_companion_prompt_is_preserved_byte_for_byte(project_root: Path) -> None:
    renderer = _renderer()
    override = "  Execute this exact companion.\r\nKeep the newline and trailing spaces.  \n"

    packet = renderer.validate({**_request(), "companion_prompt": override}, project_root)

    assert packet["companion_prompt"] == override


@pytest.mark.parametrize("value", ["", "   ", "\r\n\t"])
def test_empty_or_whitespace_only_companion_prompt_is_rejected(
    project_root: Path, value: str
) -> None:
    renderer = _renderer()

    with pytest.raises(ValueError, match="companion_prompt"):
        renderer.validate({**_request(), "companion_prompt": value}, project_root)


def test_companion_override_changes_only_handoff_companion_content(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    default_dir = tmp_path / "default"
    override_dir = tmp_path / "override"
    override = "Use this caller-supplied companion verbatim.\n"

    default_handoff = _render(renderer, _request(), project_root, default_dir)
    override_handoff = _render(
        renderer, {**_request(), "companion_prompt": override}, project_root, override_dir
    )

    default_body = (default_dir / "PROMPT_BODY.md").read_bytes()
    override_body = (override_dir / "PROMPT_BODY.md").read_bytes()
    default_reference = (default_dir / "REFERENCE_FILES.md").read_bytes()
    override_reference = (override_dir / "REFERENCE_FILES.md").read_bytes()
    assert default_body == override_body
    assert default_reference == override_reference
    assert default_handoff["transport_request"]["companion_prompt"].encode() not in default_body
    assert default_handoff["transport_request"]["companion_prompt"].encode() not in default_reference
    assert override.encode() not in override_body
    assert override.encode() not in override_reference
    assert default_handoff["transport_request"]["companion_prompt"] != override_handoff["transport_request"]["companion_prompt"]
    assert override_handoff["transport_request"]["companion_prompt"] == override
    default_without_companion = dict(default_handoff)
    override_without_companion = dict(override_handoff)
    default_without_companion["transport_request"] = dict(default_handoff["transport_request"])
    override_without_companion["transport_request"] = dict(override_handoff["transport_request"])
    default_without_companion["transport_request"].pop("companion_prompt")
    override_without_companion["transport_request"].pop("companion_prompt")
    assert default_without_companion == override_without_companion


def test_author_remains_authoring_only_and_operator_gets_companion_contract(
    project_root: Path, tmp_path: Path
) -> None:
    renderer = _renderer()
    handoff = _render(renderer, _request(), project_root, tmp_path / "packet")
    skill_text = SKILL.read_text(encoding="utf-8")

    assert handoff["send_from_author"] is False
    assert "companion_prompt" in handoff["transport_request"]
    assert "supply the companion_prompt verbatim" in skill_text
    assert "preserve the `PROMPT_BODY.md` and" in skill_text
    assert "`REFERENCE_FILES.md` bytes unchanged" in skill_text
