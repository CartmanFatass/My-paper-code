import json
from pathlib import Path
import subprocess

import pytest

from tools import codex_wait_probe as probe


def test_result_identity_and_terminal_states(tmp_path):
    path = tmp_path / "result.json"
    assert probe.result_json(path, "accepted-7")["state"] == "running"
    for state in ("running", "complete", "failed", "blocked", "unknown"):
        path.write_text(json.dumps({"operation_id": "accepted-7", "state": state}))
        assert probe.result_json(path, "accepted-7")["state"] == state
    assert probe.result_json(path, "different-operation")["state"] == "blocked"


def test_invalid_or_partial_output_is_unknown(tmp_path, capsys):
    path = tmp_path / "result.json"
    path.write_text('{"state":')
    probe.main(["result-json", "--path", str(path), "--expected-id", "accepted-7"])
    assert json.loads(capsys.readouterr().out)["state"] == "unknown"
    path.write_text(json.dumps({"operation_id": "accepted-7", "exit_code": 0}))
    probe.main(["result-json", "--path", str(path), "--expected-id", "accepted-7"])
    assert json.loads(capsys.readouterr().out)["state"] == "unknown"


@pytest.fixture
def repository(tmp_path):
    repo, remote = tmp_path / "repo", tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL,
                                       text=True).strip()
    git("config", "user.name", "Wait Test")
    git("config", "user.email", "wait@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", "/dev/null")
    git("remote", "add", "origin", str(remote))
    (repo / "public.md").write_text("initial\n")
    git("add", "public.md")
    git("commit", "-m", "initial")
    git("push", "origin", "main")
    baseline = git("rev-parse", "HEAD")
    return repo, git, baseline


def read(repo, baseline, path="public.md"):
    return probe.git_publication(repo, "origin", "refs/heads/main", path, baseline)


def test_publication_ignores_dirty_unpushed_and_unrelated_changes(repository):
    repo, git, baseline = repository
    assert read(repo, baseline)["state"] == "running"
    (repo / "other.md").write_text("unrelated")
    git("add", "other.md"); git("commit", "-m", "other"); git("push", "origin", "main")
    assert read(repo, baseline)["state"] == "running"
    (repo / "public.md").write_text("public evidence updated\n")
    assert read(repo, baseline)["state"] == "running"
    git("add", "public.md"); git("commit", "-m", "new evidence")
    assert read(repo, baseline)["state"] == "running"
    git("push", "origin", "main")
    value = read(repo, baseline)
    assert value["state"] == "complete"
    assert value["source_sha"] == git("rev-parse", "HEAD")
    assert value["baseline_blob"] != value["published_blob"]
    assert "may still be incomplete" in value["meaning"]


def test_deleted_or_new_file_is_a_publication_change(repository):
    repo, git, baseline = repository
    assert read(repo, baseline, "new.md")["state"] == "running"
    (repo / "new.md").write_text("new")
    git("add", "new.md"); git("rm", "public.md"); git("commit", "-m", "replace")
    git("push", "origin", "main")
    assert read(repo, baseline, "new.md")["state"] == "complete"
    assert read(repo, baseline)["published_blob"] is None


def test_missing_published_commit_is_unknown_and_does_not_fetch(repository, tmp_path, capsys):
    repo, git, baseline = repository
    other = tmp_path / "other-clone"
    subprocess.run(["git", "clone", "--branch", "main", str(repo.parent / "remote.git"), str(other)],
                   check=True, capture_output=True)
    (repo / "public.md").write_text("new")
    git("add", "public.md"); git("commit", "-m", "new"); git("push", "origin", "main")
    probe.main(["git-publication", "--repo", str(other), "--path", "public.md", "--baseline", baseline])
    assert json.loads(capsys.readouterr().out)["state"] == "unknown"
    assert subprocess.check_output(["git", "-C", str(other), "rev-parse", "HEAD"], text=True).strip() == baseline


@pytest.mark.parametrize("path", ["../secret", "/absolute", "", "./public.md"])
def test_bad_publication_path_refused_before_query(tmp_path, path):
    with pytest.raises(ValueError):
        read(tmp_path, "a" * 40, path)
