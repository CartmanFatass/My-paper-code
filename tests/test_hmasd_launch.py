from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import pytest

from scripts import hmasd_admission, hmasd_launch


ROOT = Path(__file__).resolve().parents[1]
SAFE_SNAPSHOT = {
    "schema_version": 1,
    "preflight_id": "fixture-preflight",
    "captured_at": "2026-09-17T00:00:00Z",
    "host_identity": "fixture-host",
    "memory": {
        "measurement_source": "fixture",
        "total_bytes": 16 * 1024**3,
        "available_bytes": 12 * 1024**3,
        "cgroup_memory_max_raw": "max",
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
    },
}


def _run(*command: str, cwd: Path, check: bool = True, env=None):
    return subprocess.run(
        list(command),
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30,
    )


def _git(root: Path, *arguments: str, check: bool = True):
    return _run("git", *arguments, cwd=root, check=check)


def _research(*, pause: str = "lifted", lead: str = "Codex DM") -> str:
    return f"""# HMASD research index

**Owner pause: {pause}** since fixture time.

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `demo_direction` | Fixture? | exploring | {lead} | Fixture only. |

## Reserve
"""


RUNNER = """from __future__ import annotations
import argparse
import json
from pathlib import Path
from hmasd_admission import require_admission

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
admission = require_admission(__file__, direction='demo_direction')
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
(output / 'summary.json').write_text(json.dumps({'sha': admission['sha']}), encoding='utf-8')
"""


REPLAY_RUNNER = """from __future__ import annotations
import argparse
from pathlib import Path
from hmasd_admission import AdmissionRefused, require_admission

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
require_admission(__file__, direction='demo_direction')
try:
    require_admission(__file__, direction='demo_direction')
except AdmissionRefused as exc:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'replay-refused.txt').write_text(str(exc), encoding='utf-8')
"""


ATEXIT_RUNNER = """from __future__ import annotations
import argparse
import atexit
import os
from hmasd_admission import require_admission

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
require_admission(__file__, direction='demo_direction')
atexit.register(os._exit, 17)
"""


THREAD_RUNNER = """from __future__ import annotations
import argparse
from pathlib import Path
import threading
import time
from hmasd_admission import require_admission

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
require_admission(__file__, direction='demo_direction')
def finish_later():
    time.sleep(3.0)
    (Path(args.output) / 'thread-finished').write_text('done', encoding='utf-8')
threading.Thread(target=finish_later, daemon=False).start()
"""


@pytest.fixture
def launch_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    (source / "scripts").mkdir(parents=True)
    (source / "docs" / "research").mkdir(parents=True)
    (source / ".codex").mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts" / "hmasd_admission.py", source / "scripts" / "hmasd_admission.py")
    (source / "scripts" / "fixture_runner.py").write_text(RUNNER, encoding="utf-8")
    (source / "scripts" / "replay_runner.py").write_text(REPLAY_RUNNER, encoding="utf-8")
    (source / "scripts" / "atexit_runner.py").write_text(ATEXIT_RUNNER, encoding="utf-8")
    (source / "scripts" / "thread_runner.py").write_text(THREAD_RUNNER, encoding="utf-8")
    (source / "scripts" / "unguarded_runner.py").write_text(
        "from pathlib import Path\nPath('unguarded-effect').write_text('bad')\n",
        encoding="utf-8",
    )
    (source / "docs" / "research" / "RESEARCH.md").write_text(
        _research(), encoding="utf-8"
    )
    configured_python = Path(sys.executable).resolve().as_posix()
    configured_root = source.resolve().as_posix()
    (source / ".codex" / "hmasd-compute.toml").write_text(
        f'''schema_version = 1
status = "active"
control_plane_node = "fixture"

[nodes.fixture]
role = "test"
project_root = "{configured_root}"
python = "{configured_python}"
''',
        encoding="utf-8",
    )
    (source / ".gitignore").write_text("runs/\n__pycache__/\n*.pyc\n", encoding="utf-8")
    _git(source.parent, "init", "-b", "main", str(source))
    _git(source, "config", "user.email", "fixture@example.invalid")
    _git(source, "config", "user.name", "Fixture")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "fixture")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(source, "remote", "add", "origin", str(remote))
    _git(source, "push", "-u", "origin", "main")
    sha = _git(source, "rev-parse", "HEAD").stdout.strip()
    return source, remote, sha


def _arguments(source: Path, sha: str, tag: str = "attempt-a") -> argparse.Namespace:
    output = source / "runs" / "demo_direction" / tag
    return argparse.Namespace(
        direction="demo_direction",
        lead="Codex DM",
        sha=sha,
        output=str(output),
        source_root=str(source),
        node="fixture",
        remote="origin",
        admission_timeout_seconds=10.0,
        runner_argv=[
            "scripts/fixture_runner.py",
            "--output",
            str(output),
        ],
    )


def _wait_for(path: Path, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {path}")


@pytest.mark.parametrize("pause", ["in force", "unknown", ""])
def test_pause_state_fails_closed(pause: str) -> None:
    text = _research(pause=pause) if pause else _research().replace(
        "**Owner pause: lifted** since fixture time.\n", ""
    )
    if pause == "lifted":
        assert hmasd_launch.parse_research_state(text, "demo_direction")[0] == "lifted"
    else:
        with pytest.raises(hmasd_launch.LaunchRefusal, match="pause"):
            observed, _state = hmasd_launch.parse_research_state(text, "demo_direction")
            if observed == "in force":
                raise hmasd_launch.LaunchRefusal("owner pause is in force")


def test_ambiguous_pause_and_wrong_lead_are_refused(tmp_path: Path) -> None:
    ambiguous = _research() + "\n**Owner pause: lifted** duplicate.\n"
    with pytest.raises(hmasd_launch.LaunchRefusal, match="exactly one"):
        hmasd_launch.parse_research_state(ambiguous, "demo_direction")

    control = tmp_path / "control"
    (control / "docs" / "research").mkdir(parents=True)
    (control / "docs" / "research" / "RESEARCH.md").write_text(
        _research(lead="Claude session"), encoding="utf-8"
    )
    with pytest.raises(hmasd_launch.LaunchRefusal, match="lead mismatch"):
        hmasd_launch._require_policy(control, "demo_direction", "Codex DM")


def test_git_common_control_cannot_be_redirected(
    launch_repo: tuple[Path, Path, str], tmp_path: Path
) -> None:
    source, _remote, _sha = launch_repo
    other = tmp_path / "other"
    _git(tmp_path, "init", "-b", "main", str(other))
    with pytest.raises(hmasd_launch.LaunchRefusal, match="conflicts"):
        hmasd_launch._resolve_control_root(source, source, other)


def test_stale_lifted_control_is_refused_when_published_control_is_paused(
    launch_repo: tuple[Path, Path, str], tmp_path: Path
) -> None:
    source, remote, _sha = launch_repo
    publisher = tmp_path / "publisher"
    _git(tmp_path, "clone", "-b", "main", str(remote), str(publisher))
    _git(publisher, "config", "user.email", "fixture@example.invalid")
    _git(publisher, "config", "user.name", "Fixture")
    research = publisher / "docs" / "research" / "RESEARCH.md"
    research.write_text(_research(pause="in force"), encoding="utf-8")
    _git(publisher, "add", "docs/research/RESEARCH.md")
    _git(publisher, "commit", "-m", "pause")
    _git(publisher, "push", "origin", "main")
    _git(source, "fetch", "origin")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="differs from the fresh published"):
        hmasd_launch._require_policy(source, "demo_direction", "Codex DM", "origin")


def test_wrong_sha_dirty_tree_and_unpublished_commit_are_refused(
    launch_repo: tuple[Path, Path, str]
) -> None:
    source, _remote, sha = launch_repo
    with pytest.raises(hmasd_launch.LaunchRefusal, match="source HEAD"):
        hmasd_launch._validate_source(source, "0" * 40, "origin")

    tracked = source / "scripts" / "fixture_runner.py"
    tracked.write_text(tracked.read_text(encoding="utf-8") + "\n# dirty\n", encoding="utf-8")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="source inputs"):
        hmasd_launch._validate_source(source, sha, "origin")


def test_unpublished_head_is_refused(launch_repo: tuple[Path, Path, str]) -> None:
    source, _remote, _sha = launch_repo
    marker = source / "published-input.txt"
    marker.write_text("not pushed\n", encoding="utf-8")
    _git(source, "add", "published-input.txt")
    _git(source, "commit", "-m", "not pushed")
    unpublished = _git(source, "rev-parse", "HEAD").stdout.strip()
    with pytest.raises(hmasd_launch.LaunchRefusal, match="not contained"):
        hmasd_launch._validate_source(source, unpublished, "origin")


def test_pruned_stale_remote_ref_cannot_certify_publication(
    launch_repo: tuple[Path, Path, str]
) -> None:
    source, _remote, _sha = launch_repo
    _git(source, "checkout", "-b", "stale-publication")
    marker = source / "stale-only.txt"
    marker.write_text("only on deleted branch\n", encoding="utf-8")
    _git(source, "add", "stale-only.txt")
    _git(source, "commit", "-m", "stale only")
    stale_sha = _git(source, "rev-parse", "HEAD").stdout.strip()
    _git(source, "push", "origin", "stale-publication")
    _git(source, "push", "origin", "--delete", "stale-publication")
    _git(source, "update-ref", "refs/remotes/origin/stale-publication", stale_sha)
    assert _git(
        source,
        "show-ref",
        "--verify",
        "refs/remotes/origin/stale-publication",
        check=False,
    ).returncode == 0
    with pytest.raises(hmasd_launch.LaunchRefusal, match="not contained"):
        hmasd_launch._validate_source(source, stale_sha, "origin")
    assert _git(
        source,
        "show-ref",
        "--verify",
        "refs/remotes/origin/stale-publication",
        check=False,
    ).returncode != 0


def test_claim_identity_is_worktree_and_output_spelling_independent(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for root in (first, second):
        (root / "scripts").mkdir(parents=True)
        (root / "inputs").mkdir()
        (root / "scripts" / "runner.py").write_text("pass\n", encoding="utf-8")
        (root / "inputs" / "data.json").write_text("{}\n", encoding="utf-8")
        (root / "inputs" / "summary.json").write_text("{}\n", encoding="utf-8")
    first_output = first / "runs" / "demo_direction" / "one"
    second_output = second / "runs" / "demo_direction" / "two"
    first_identity = hmasd_launch._command_identity(
        Path(sys.executable),
        first / "scripts" / "runner.py",
        [
            "--output",
            str(first_output),
            "--data",
            str(first / "inputs" / "data.json"),
            f"--generic-summary={first / 'inputs' / 'summary.json'}",
        ],
        first_output,
        first,
    )
    second_identity = hmasd_launch._command_identity(
        Path(sys.executable),
        second / "scripts" / "runner.py",
        [
            f"--out={second_output}",
            "--data",
            str(second / "inputs" / "data.json"),
            f"--generic-summary={second / 'inputs' / 'summary.json'}",
        ],
        second_output,
        second,
    )
    assert first_identity == second_identity
    assert first_identity[1:] == [
        "scripts/runner.py",
        "--data",
        "<SOURCE>/inputs/data.json",
        "--generic-summary=<SOURCE>/inputs/summary.json",
    ]


def test_untracked_source_and_unguarded_runner_are_refused(
    launch_repo: tuple[Path, Path, str]
) -> None:
    source, _remote, sha = launch_repo
    with pytest.raises(hmasd_launch.LaunchRefusal, match="exactly one require_admission"):
        hmasd_launch._validate_guard_contract(
            source / "scripts" / "unguarded_runner.py", "demo_direction"
        )
    (source / "scripts" / "shadow_module.py").write_text("VALUE = 'shadow'\n", encoding="utf-8")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="untracked source inputs"):
        hmasd_launch._validate_source(source, sha, "origin")


def test_successful_fixture_is_admitted_and_detached(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha)
    manifest = hmasd_launch.launch(args)
    output = Path(args.output)
    _wait_for(output / "summary.json")
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["sha"] == sha
    assert manifest["acceptance"] == "accepted"
    assert manifest["process"]["pid"] > 0
    assert json.loads((output / "launch-status.json").read_text())["status"] == "accepted"
    assert json.loads((output / "admission-preflight.json").read_text())["passed"] is True
    _wait_for(output / "process-exit.json")
    process_exit = json.loads((output / "process-exit.json").read_text())
    assert process_exit["exit_code"] == 0
    assert process_exit["termination"] == "process_exit"
    assert process_exit["process_identity"] == manifest["runner_process"]["identity"]


def test_memory_failure_never_releases_child(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    unsafe = {
        **SAFE_SNAPSHOT,
        "memory": {**SAFE_SNAPSHOT["memory"], "available_bytes": 1024**3},
    }
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: unsafe,
    )
    args = _arguments(source, sha, "memory-refused")
    with pytest.raises(hmasd_launch.LaunchRefusal) as caught:
        hmasd_launch.launch(args)
    assert caught.value.exit_code == 6
    output = Path(args.output)
    assert not (output / "summary.json").exists()
    assert json.loads((output / "launch-status.json").read_text())["status"] == "preflight_refused"


def test_supervisor_records_actual_exit_after_atexit_changes_code(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "atexit-exit")
    args.runner_argv[0] = "scripts/atexit_runner.py"
    manifest = hmasd_launch.launch(args)
    witness = Path(args.output) / "process-exit.json"
    _wait_for(witness)
    payload = json.loads(witness.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 17
    assert payload["process_identity"] == manifest["runner_process"]["identity"]


def test_exit_witness_waits_for_non_daemon_thread(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "thread-exit")
    args.runner_argv[0] = "scripts/thread_runner.py"
    hmasd_launch.launch(args)
    output = Path(args.output)
    assert not (output / "process-exit.json").exists()
    _wait_for(output / "thread-finished")
    _wait_for(output / "process-exit.json")
    assert json.loads((output / "process-exit.json").read_text())["exit_code"] == 0


def test_pause_change_after_spawn_is_denied_before_preflight(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    real_spawn = hmasd_launch._spawn
    preflight_called = False

    def spawn_then_pause(*args, **kwargs):
        process = real_spawn(*args, **kwargs)
        (source / "docs" / "research" / "RESEARCH.md").write_text(
            _research(pause="in force"), encoding="utf-8"
        )
        return process

    def capture():
        nonlocal preflight_called
        preflight_called = True
        return SAFE_SNAPSHOT

    monkeypatch.setattr(hmasd_launch, "_spawn", spawn_then_pause)
    monkeypatch.setattr(hmasd_launch.hmasd_resource_preflight, "capture_snapshot", capture)
    args = _arguments(source, sha, "pause-race")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="pause"):
        hmasd_launch.launch(args)
    assert preflight_called is False
    assert not (Path(args.output) / "summary.json").exists()


def test_source_change_after_spawn_is_denied_before_preflight(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    real_spawn = hmasd_launch._spawn
    preflight_called = False

    def spawn_then_mutate(*args, **kwargs):
        process = real_spawn(*args, **kwargs)
        runner = source / "scripts" / "fixture_runner.py"
        runner.write_text(runner.read_text(encoding="utf-8") + "\n# raced\n", encoding="utf-8")
        return process

    def capture():
        nonlocal preflight_called
        preflight_called = True
        return SAFE_SNAPSHOT

    monkeypatch.setattr(hmasd_launch, "_spawn", spawn_then_mutate)
    monkeypatch.setattr(hmasd_launch.hmasd_resource_preflight, "capture_snapshot", capture)
    args = _arguments(source, sha, "source-race")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="source inputs"):
        hmasd_launch.launch(args)
    assert preflight_called is False
    assert not (Path(args.output) / "summary.json").exists()


def test_duplicate_claim_cannot_be_bypassed_with_new_output(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    first = _arguments(source, sha, "first-output")
    hmasd_launch.launch(first)
    _wait_for(Path(first.output) / "summary.json")
    second = _arguments(source, sha, "renamed-output")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="duplicate or uncertain") as caught:
        hmasd_launch.launch(second)
    assert caught.value.exit_code == 5
    assert not Path(second.output).exists()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "missing HMASD admission"),
        ("expired", "expired"),
        ("direction", "direction mismatch"),
        ("command", "command does not match"),
    ],
)
def test_runner_rejects_missing_expired_and_mismatched_admission(
    launch_repo: tuple[Path, Path, str], mutation: str, message: str
) -> None:
    source, _remote, sha = launch_repo
    runner = source / "scripts" / "fixture_runner.py"
    output = source / "runs" / "demo_direction" / f"reject-{mutation}"
    arguments = ["--output", str(output)]
    environment = dict(os.environ)
    if mutation != "missing":
        spec = {
            "schema_version": 1,
            "endpoint": ["127.0.0.1", 9],
            "nonce": "fixture-nonce",
            "expires_at": time.time() - 1 if mutation == "expired" else time.time() + 30,
            "direction": "other_direction" if mutation == "direction" else "demo_direction",
            "python": str(Path(sys.executable).resolve()),
            "runner": str(runner.resolve()),
            "source_root": str(source.resolve()),
            "sha": sha,
            "command_sha256": (
                "0" * 64
                if mutation == "command"
                else hmasd_admission.command_digest(sys.executable, runner, arguments)
            ),
            "parent_pid": os.getpid(),
        }
        environment[hmasd_admission.ENVIRONMENT_KEY] = json.dumps(spec)
    completed = _run(
        sys.executable,
        str(runner),
        *arguments,
        cwd=source,
        check=False,
        env=environment,
    )
    assert completed.returncode != 0
    assert message in completed.stderr
    assert not (output / "summary.json").exists()


def test_runner_admission_is_single_use(launch_repo: tuple[Path, Path, str]) -> None:
    source, _remote, sha = launch_repo
    runner = source / "scripts" / "replay_runner.py"
    output = source / "runs" / "demo_direction" / "replay"
    arguments = ["--output", str(output)]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(10)
        nonce = "fixture-single-use"
        spec = {
            "schema_version": 1,
            "endpoint": ["127.0.0.1", listener.getsockname()[1]],
            "nonce": nonce,
            "expires_at": time.time() + 30,
            "direction": "demo_direction",
            "python": str(Path(sys.executable).resolve()),
            "runner": str(runner.resolve()),
            "source_root": str(source.resolve()),
            "sha": sha,
            "command_sha256": hmasd_admission.command_digest(
                sys.executable, runner, arguments
            ),
            "parent_pid": os.getpid(),
        }
        environment = dict(os.environ)
        environment[hmasd_admission.ENVIRONMENT_KEY] = json.dumps(spec)
        process = subprocess.Popen(
            [sys.executable, str(runner), *arguments],
            cwd=source,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        peer, _address = listener.accept()
        with peer, peer.makefile("rwb", buffering=0) as stream:
            hello = json.loads(stream.readline().decode("utf-8"))
            assert hello["pid"] == process.pid
            stream.write(
                (json.dumps({"kind": "grant", "nonce": nonce, "pid": process.pid}) + "\n").encode()
            )
            stream.flush()
            accepted = json.loads(stream.readline().decode("utf-8"))
            assert accepted["kind"] == "accepted"
        stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, (stdout, stderr)
    assert "single-use" in (output / "replay-refused.txt").read_text(encoding="utf-8")
