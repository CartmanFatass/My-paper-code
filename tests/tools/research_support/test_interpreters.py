"""Host interpreter selection follows the tracked compute configuration."""

from pathlib import Path

import pytest

from tools.research_support import interpreters


def _config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
    path = tmp_path / "compute.toml"
    path.write_text(body, encoding="utf-8")
    monkeypatch.setattr(interpreters, "_CONFIG_PATH", path)
    return path


CONFIG = '''
status = "active"
[control_plane_by_platform]
win32 = "windows"
linux = "linux"
[nodes.windows]
python = "C:/scientific/python.exe"
control_plane_python = "C:/control/python.exe"
[nodes.linux]
python = "/opt/scientific/bin/python"
control_plane_python = "/opt/control/bin/python"
'''


@pytest.mark.parametrize(
    ("platform", "scientific", "control"),
    [
        ("win32", "C:/scientific/python.exe", "C:/control/python.exe"),
        ("linux", "/opt/scientific/bin/python", "/opt/control/bin/python"),
    ],
)
def test_platform_nodes_and_independent_roles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str, scientific: str, control: str
) -> None:
    _config(tmp_path, monkeypatch, CONFIG)
    monkeypatch.setattr(interpreters, "_platform_key", lambda: platform)
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR, raising=False)
    monkeypatch.delenv(interpreters.CONTROL_PLANE_ENV_VAR, raising=False)
    assert interpreters.scientific_interpreter() == scientific
    assert interpreters.control_plane_interpreter() == control


def test_config_changes_are_read_and_cwd_does_not_select_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _config(tmp_path, monkeypatch, CONFIG)
    monkeypatch.setattr(interpreters, "_platform_key", lambda: "linux")
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    assert interpreters.scientific_interpreter() == "/opt/scientific/bin/python"
    path.write_text(CONFIG.replace("/opt/scientific/bin/python", "/new/science/python"), encoding="utf-8")
    assert interpreters.scientific_interpreter() == "/new/science/python"


def test_overrides_work_even_without_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(interpreters, "_CONFIG_PATH", tmp_path / "absent.toml")
    monkeypatch.setattr(interpreters, "_platform_key", lambda: "linux")
    monkeypatch.setenv(interpreters.SCIENTIFIC_ENV_VAR, "/custom/science")
    monkeypatch.setenv(interpreters.CONTROL_PLANE_ENV_VAR, "/custom/control")
    assert interpreters.scientific_interpreter() == "/custom/science"
    assert interpreters.control_plane_interpreter() == "/custom/control"
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR)
    with pytest.raises(ValueError, match="cannot read compute configuration"):
        interpreters.scientific_interpreter()


def test_unsupported_platform_is_explicitly_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path, monkeypatch, CONFIG)
    monkeypatch.setattr(interpreters, "_platform_key", lambda: "darwin")
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR, raising=False)
    monkeypatch.delenv(interpreters.CONTROL_PLANE_ENV_VAR, raising=False)
    assert interpreters.scientific_interpreter() == ""
    assert interpreters.control_plane_interpreter() == ""
    assert not interpreters.interpreter_is_present("")
    assert interpreters.describe_host()["scientific_interpreter_source"] == "unsupported platform"


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ("not valid [", "cannot read compute configuration"),
        (CONFIG.replace('status = "active"', 'status = "inactive"'), "missing or inactive"),
        (CONFIG.replace('linux = "linux"', 'linux = "missing"'), "no node 'missing'"),
        (CONFIG.replace('[nodes.linux]', '[nodes.linux]\nenabled = false'), "is disabled"),
        (CONFIG.replace('control_plane_python = "/opt/control/bin/python"', ""), "lacks control_plane_python"),
        (CONFIG.replace('python = "/opt/scientific/bin/python"', ""), "lacks python"),
        (CONFIG.replace('linux = "linux"', ""), "no control-plane node for linux"),
    ],
)
def test_invalid_configuration_has_explicit_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config: str, message: str
) -> None:
    _config(tmp_path, monkeypatch, config)
    monkeypatch.setattr(interpreters, "_platform_key", lambda: "linux")
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR, raising=False)
    monkeypatch.delenv(interpreters.CONTROL_PLANE_ENV_VAR, raising=False)
    role = interpreters.control_plane_interpreter if "control_plane_python" in message else interpreters.scientific_interpreter
    with pytest.raises(ValueError, match=message):
        role()


def test_real_config_is_checkout_relative_even_from_another_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(interpreters.SCIENTIFIC_ENV_VAR, raising=False)
    monkeypatch.delenv(interpreters.CONTROL_PLANE_ENV_VAR, raising=False)
    assert interpreters._CONFIG_PATH == Path(__file__).resolve().parents[3] / ".codex" / "hmasd-compute.toml"
    foreign_config = tmp_path / ".codex" / "hmasd-compute.toml"
    foreign_config.parent.mkdir()
    foreign_config.write_text(CONFIG, encoding="utf-8")
    for platform in ("linux", "win32"):
        monkeypatch.setattr(interpreters, "_platform_key", lambda: platform)
        expected = (interpreters.scientific_interpreter(), interpreters.control_plane_interpreter())
        assert all(expected)
        monkeypatch.chdir(tmp_path)
        assert (interpreters.scientific_interpreter(), interpreters.control_plane_interpreter()) == expected
