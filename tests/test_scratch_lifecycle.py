"""Exercise cleanup in real child pytest processes, without touching old scratch."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def isolated_suite(tmp_path):
    suite = tmp_path / "checkout"
    tests = suite / "tests"
    tests.mkdir(parents=True)
    shutil.copyfile(Path(__file__).with_name("conftest.py"), tests / "conftest.py")
    (suite / "pytest.ini").write_text("[pytest]\naddopts = -p no:cacheprovider\n")
    return suite


def run_suite(suite, *args):
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    env.pop("PYTEST_ADDOPTS", None)
    return subprocess.run([sys.executable, "-m", "pytest", "-q", *args, "tests"],
                          cwd=suite, env=env, text=True, capture_output=True)


@pytest.mark.parametrize("outcome,code", [("True", 0), ("False", 1)])
def test_success_and_failure_clean_own_scratch(isolated_suite, outcome, code):
    suite = isolated_suite
    (suite / "tests/test_probe.py").write_text(
        "from pathlib import Path\n"
        "def test_probe(tmp_path):\n"
        "    (tmp_path / 'data').write_text('scratch')\n"
        "    Path('observed.txt').write_text(str(tmp_path))\n"
        f"    assert {outcome}\n"
    )
    result = run_suite(suite)
    assert result.returncode == code, result.stdout + result.stderr
    observed = Path((suite / "observed.txt").read_text())
    assert observed.is_relative_to(suite / "temp/tests")
    assert not observed.exists()
    assert list((suite / "temp/tests").iterdir()) == []


def test_explicit_new_directory_is_cleaned(isolated_suite):
    suite = isolated_suite
    (suite / "tests/test_probe.py").write_text("def test_probe(tmp_path):\n    assert tmp_path.exists()\n")
    result = run_suite(suite, "--basetemp", "temp/directions/example/test/new-tag")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (suite / "temp/directions/example/test/new-tag").exists()


def test_collection_failure_cleans_scratch(isolated_suite):
    suite = isolated_suite
    (suite / "tests/test_probe.py").write_text("raise RuntimeError('collection failure')\n")
    result = run_suite(suite)
    assert result.returncode == 2, result.stdout + result.stderr
    assert list((suite / "temp/tests").iterdir()) == []


def test_new_external_directory_is_not_created(isolated_suite):
    suite = isolated_suite
    result = run_suite(suite, "--basetemp", str(suite.parent / "outside-new"))
    assert result.returncode == 4, result.stdout + result.stderr
    assert not (suite.parent / "outside-new").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows copied read-only attributes")
def test_readonly_copied_files_and_directories_are_cleaned(isolated_suite):
    suite = isolated_suite
    (suite / "tests/test_probe.py").write_text(
        "import os, stat\n"
        "def test_probe(tmp_path):\n"
        "    folder = tmp_path / 'copied'\n"
        "    folder.mkdir()\n"
        "    file = folder / 'data'\n"
        "    file.write_text('copy')\n"
        "    os.chmod(file, stat.S_IREAD)\n"
        "    os.chmod(folder, stat.S_IREAD)\n"
    )
    result = run_suite(suite)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "cleanup failed" not in result.stderr
    assert list((suite / "temp/tests").iterdir()) == []


@pytest.mark.parametrize("location", ["temp/existing", "outside", "temp"])
def test_existing_or_external_directory_is_preserved(isolated_suite, location):
    suite = isolated_suite
    target = suite / location
    target.mkdir(parents=True)
    sentinel = target / "sentinel.txt"
    sentinel.write_text("preserve")
    (suite / "tests/test_probe.py").write_text("def test_probe():\n    pass\n")
    result = run_suite(suite, "--basetemp", str(target))
    assert result.returncode == 4, result.stdout + result.stderr
    assert sentinel.read_text() == "preserve"
