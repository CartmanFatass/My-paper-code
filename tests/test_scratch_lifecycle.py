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


@pytest.mark.parametrize("failure", ["assert False", "raise RuntimeError('collection')"])
def test_opt_in_retains_failure_evidence(isolated_suite, failure):
    suite = isolated_suite
    source = ("def test_probe(tmp_path):\n    (tmp_path / 'evidence').write_text('diagnostic')\n"
              "    assert False\n") if failure == "assert False" else failure
    (suite / "tests/test_probe.py").write_text(source)
    result = run_suite(suite, "--keep-scratch-on-failure")
    assert result.returncode != 0
    assert "scratch retained by request" in result.stderr
    assert len(list((suite / "temp/tests").iterdir())) == 1


def test_retention_option_still_cleans_success(isolated_suite):
    (isolated_suite / "tests/test_probe.py").write_text("def test_probe(tmp_path):\n    pass\n")
    result = run_suite(isolated_suite, "--keep-scratch-on-failure")
    assert result.returncode == 0, result.stdout + result.stderr
    assert list((isolated_suite / "temp/tests").iterdir()) == []


@pytest.fixture
def cleanup_checkout(tmp_path):
    suite = tmp_path / "cleanup-checkout"
    (suite / "scripts").mkdir(parents=True)
    shutil.copyfile(Path(__file__).parents[1] / "scripts/cleanup_test_scratch.ps1",
                    suite / "scripts/cleanup_test_scratch.ps1")
    subprocess.run(["git", "init", str(suite)], check=True, capture_output=True)
    (suite / "temp/tests/owned").mkdir(parents=True)
    (suite / "temp/tests/owned/sentinel").write_text("fixture")
    return suite


def cleanup_probe(suite, arguments, *, busy=False):
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("PowerShell 7 not available")
    # The fixture checkout has no test producer. Model the process probe independently
    # of this parent pytest, which owns and later tears down the enclosing tmp_path.
    probe = suite / "probe.ps1"
    processes = "[pscustomobject]@{Name='pytest.exe';CommandLine='pytest';ProcessId=123}" if busy else ""
    probe.write_text("function Get-CimInstance { " + processes + " }\n"
                     "$ErrorActionPreference = 'Stop'\ntry {\n"
                     "& ./scripts/cleanup_test_scratch.ps1 " + arguments + " | ForEach-Object { $_ | ConvertTo-Json -Compress }\n"
                     "} catch { Write-Output $_; exit 1 }\n")
    return subprocess.run([pwsh, "-NoProfile", "-File", str(probe)], cwd=suite,
                          capture_output=True, text=True)


def test_cleanup_requires_explicit_delete_target(cleanup_checkout):
    result = cleanup_probe(cleanup_checkout, "-Delete")
    assert result.returncode != 0
    assert "explicit" in result.stdout
    assert (cleanup_checkout / "temp/tests/owned/sentinel").exists()


def test_cleanup_preview_delete_and_absent(cleanup_checkout):
    result = cleanup_probe(cleanup_checkout, "-RunDirectory temp/tests/owned")
    assert result.returncode == 0 and 'Preview' in result.stdout
    assert (cleanup_checkout / "temp/tests/owned/sentinel").exists()
    result = cleanup_probe(cleanup_checkout, "-RunDirectory temp/tests/owned -Delete")
    assert result.returncode == 0 and 'Deleted' in result.stdout
    result = cleanup_probe(cleanup_checkout, "-RunDirectory temp/tests/owned -Delete")
    assert result.returncode == 0 and 'AlreadyAbsent' in result.stdout


def test_cleanup_reports_each_target_and_preserves_tracked(cleanup_checkout):
    subprocess.run(["git", "-C", str(cleanup_checkout), "add", "temp/tests/owned/sentinel"], check=True)
    result = cleanup_probe(cleanup_checkout,
                           "-RunDirectory @('temp/tests/owned','temp/tests/missing','../outside') -Delete")
    assert result.returncode != 0
    assert 'tracked content' in result.stdout and 'AlreadyAbsent' in result.stdout
    assert 'Not a single test invocation' in result.stdout
    assert (cleanup_checkout / "temp/tests/owned/sentinel").exists()


def test_cleanup_busy_preserves_target(cleanup_checkout):
    result = cleanup_probe(cleanup_checkout, "-RunDirectory temp/tests/owned -Delete", busy=True)
    assert result.returncode != 0 and 'Tests may still be running' in result.stdout
    assert (cleanup_checkout / "temp/tests/owned/sentinel").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows case-insensitive paths")
def test_cleanup_mixed_case_cannot_hide_tracked_content(cleanup_checkout):
    subprocess.run(["git", "-C", str(cleanup_checkout), "add", "temp/tests/owned/sentinel"], check=True)
    result = cleanup_probe(cleanup_checkout, "-RunDirectory TEMP/TESTS/OWNED -Delete")
    assert result.returncode != 0 and 'tracked content' in result.stdout
    assert (cleanup_checkout / "temp/tests/owned/sentinel").exists()


def test_review_fixture_requires_explicit_mode_and_preserves_default_preview(cleanup_checkout):
    review = cleanup_checkout / 'temp/scratch-review-fixture'
    review.mkdir()
    (review / 'sentinel').write_text('owned fixture')
    refused = cleanup_probe(cleanup_checkout, '-RunDirectory temp/scratch-review-fixture -Delete')
    assert refused.returncode != 0 and review.exists()
    preview = cleanup_probe(cleanup_checkout, '-ReviewFixture -RunDirectory temp/scratch-review-fixture')
    assert preview.returncode == 0 and 'Preview' in preview.stdout and review.exists()
    deleted = cleanup_probe(cleanup_checkout, '-ReviewFixture -RunDirectory temp/scratch-review-fixture -Delete')
    assert deleted.returncode == 0 and 'Deleted' in deleted.stdout and not review.exists()


@pytest.mark.parametrize('arguments', [
    '-ReviewFixture -Delete',
    '-ReviewFixture -RunDirectory temp -Delete',
    '-ReviewFixture -RunDirectory temp/scratch-review-fixture/child -Delete',
    '-ReviewFixture -RunDirectory temp/unrelated -Delete',
])
def test_review_fixture_mode_keeps_narrow_scope(cleanup_checkout, arguments):
    result = cleanup_probe(cleanup_checkout, arguments)
    assert result.returncode != 0
    assert (cleanup_checkout / 'temp/tests/owned/sentinel').exists()


def test_review_fixture_mode_keeps_tracked_and_busy_guards(cleanup_checkout):
    review = cleanup_checkout / 'temp/scratch-review-fixture'
    review.mkdir()
    (review / 'sentinel').write_text('owned fixture')
    arguments = '-ReviewFixture -RunDirectory temp/scratch-review-fixture -Delete'
    busy = cleanup_probe(cleanup_checkout, arguments, busy=True)
    assert busy.returncode != 0 and 'Tests may still be running' in busy.stdout
    subprocess.run(['git', '-C', str(cleanup_checkout), 'add', 'temp/scratch-review-fixture/sentinel'], check=True)
    tracked = cleanup_probe(cleanup_checkout, arguments)
    assert tracked.returncode != 0 and 'tracked content' in tracked.stdout
    assert (review / 'sentinel').exists()
