from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
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
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
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
import os
console = None
if os.name == 'nt':
    import ctypes
    console = ctypes.windll.kernel32.GetConsoleWindow()
print('fixture stdout', flush=True)
import sys
print('fixture stderr', file=sys.stderr, flush=True)
(output / 'summary.json').write_text(json.dumps({'sha': admission['sha'], 'console': console, 'path': os.environ.get('PATH')}), encoding='utf-8')
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

[control_source]
remote = "origin"
ref = "refs/heads/main"

[nodes.fixture]
role = "test"
project_root = "{configured_root}"
python = "{configured_python}"
path_prefix = "{configured_root}/node-bin"
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


@pytest.mark.parametrize("equals_output", [False, True])
def test_snapshot_excludes_author_edits_and_replays_original_operation(launch_repo, monkeypatch, equals_output):
    source, _remote, sha = launch_repo
    args = _arguments(source, sha, "snapshot")
    args.snapshot = True
    if equals_output:
        args.runner_argv = [args.runner_argv[0], "--output=" + args.output]
    if equals_output:
        _git(source, 'rm', 'scripts/fixture_runner.py')
    else:
        (source / 'scripts/fixture_runner.py').write_text("raise RuntimeError('author edit must never execute')")
    (source / 'untracked-input.py').write_text('not published')
    monkeypatch.setenv('PYTHONPATH', str(source))
    monkeypatch.setattr(hmasd_launch.hmasd_resource_preflight, 'capture_snapshot', lambda: dict(SAFE_SNAPSHOT))
    manifest = hmasd_launch.launch(args)
    snapshot = Path(manifest['source_root'])
    assert snapshot != source
    assert (snapshot / 'scripts/fixture_runner.py').read_text() == RUNNER
    assert not (snapshot / 'untracked-input.py').exists()
    assert Path(manifest['output_root']) == Path(args.output)
    _wait_for(Path(args.output) / 'process-exit.json')
    assert json.loads((Path(args.output) / 'summary.json').read_text())['sha'] == sha
    before = _git(source, 'worktree', 'list', '--porcelain').stdout
    repeated = hmasd_launch.launch(args)
    assert repeated['operation_ref'] == manifest['operation_ref']
    assert repeated['request_resolution'] == 'existing_operation'
    assert _git(source, 'worktree', 'list', '--porcelain').stdout == before


def test_recovery_identity_survives_external_input_removal(launch_repo, monkeypatch):
    source, _remote, sha = launch_repo
    args = _arguments(source, sha)
    path = source / 'generic.json'
    path.write_text('{}')
    args.runner_argv += ['--generic-summary', 'generic.json', '--generic-summary-sha256', 'a' * 64]
    probe = hmasd_launch._probe_launch_request(args, sha)
    key = hmasd_launch._claim_key(args.direction, sha, ['fixture-python', *probe.identity_command_tail])
    with hmasd_launch._claim_lock(probe.git_common_dir) as store:
        claim = store / (key + '.json')
        hmasd_launch._atomic_write_json(claim, {
            'claim_key': key, 'direction': args.direction, 'sha': sha,
            'output_root': args.output, 'identity_command': ['fixture-python', *probe.identity_command_tail],
            'status': 'spawn_failed', 'acceptance': 'not_released',
        })
    path.rename(source / 'moved-generic.json')
    monkeypatch.setattr(hmasd_launch, '_prepare_paths_and_config',
                        lambda *_: pytest.fail('recovery must precede input/policy validation'))
    recovered = hmasd_launch.launch(args)
    assert recovered['operation_ref'] == str(claim)
    assert recovered['request_resolution'] == 'existing_operation'


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
    with pytest.raises(hmasd_launch.LaunchRefusal, match="fresh published control state"):
        hmasd_launch._require_policy(source, "demo_direction", "Codex DM", "origin")


def test_unrelated_local_research_prose_does_not_change_policy(
    launch_repo: tuple[Path, Path, str]
) -> None:
    source, _remote, _sha = launch_repo
    research = source / "docs" / "research" / "RESEARCH.md"
    research.write_text(
        research.read_text(encoding="utf-8") + "\nUnrelated local maintenance note.\n",
        encoding="utf-8",
    )
    state, digest = hmasd_launch._require_policy(
        source, "demo_direction", "Codex DM", "origin"
    )
    assert state == hmasd_launch.DirectionState(
        direction="demo_direction", state="exploring", lead="Codex DM"
    )
    assert digest == hmasd_launch._policy_digest(state)


def test_duplicate_active_direction_is_refused() -> None:
    text = _research().replace(
        "## Reserve",
        "| `demo_direction` | Duplicate? | exploring | Codex DM | Duplicate. |\n\n## Reserve",
    )
    with pytest.raises(hmasd_launch.LaunchRefusal, match="exactly once"):
        hmasd_launch.parse_research_state(text, "demo_direction")


def test_switched_checkout_branch_cannot_replace_pinned_control_ref(
    launch_repo: tuple[Path, Path, str], tmp_path: Path
) -> None:
    source, remote, _sha = launch_repo
    _git(source, "checkout", "-b", "local-lifted-decoy")
    publisher = tmp_path / "publisher-pinned"
    _git(tmp_path, "clone", "-b", "main", str(remote), str(publisher))
    _git(publisher, "config", "user.email", "fixture@example.invalid")
    _git(publisher, "config", "user.name", "Fixture")
    research = publisher / "docs" / "research" / "RESEARCH.md"
    research.write_text(_research(pause="in force"), encoding="utf-8")
    _git(publisher, "add", "docs/research/RESEARCH.md")
    _git(publisher, "commit", "-m", "pause pinned main")
    _git(publisher, "push", "origin", "main")
    _git(source, "fetch", "origin")

    with pytest.raises(hmasd_launch.LaunchRefusal, match="fresh published control state"):
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
    # The node's path_prefix reaches the real runner through the detached supervisor.
    assert summary["path"].startswith(source.resolve().as_posix() + "/node-bin" + os.pathsep)
    assert manifest["acceptance"] == "accepted"
    assert manifest["process"]["pid"] > 0
    assert json.loads((output / "launch-status.json").read_text())["status"] == "accepted"
    assert json.loads((output / "admission-preflight.json").read_text())["passed"] is True
    _wait_for(output / "process-exit.json")
    process_exit = json.loads((output / "process-exit.json").read_text())
    assert process_exit["exit_code"] == 0
    assert process_exit["termination"] == "process_exit"
    assert process_exit["process_identity"] == manifest["runner_process"]["identity"]
    if os.name == "nt":
        assert summary["console"] == 0
    assert "fixture stdout" in (output / "stdout.log").read_text()
    assert "fixture stderr" in (output / "stderr.log").read_text()


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

    monkeypatch.setattr(
        hmasd_launch,
        "_prepare_paths_and_config",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("existing operation reached new-effect gates")
        ),
    )
    recovered = hmasd_launch.launch(args)
    assert recovered["request_resolution"] == "existing_operation"
    assert recovered["admission"]["claim_state"] == "preflight_refused"
    assert recovered["explicit_retry_available"] is False


def test_spawn_failure_replay_returns_original_operation(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    args = _arguments(source, sha, "spawn-refused")

    def refuse_spawn(*_args, **_kwargs):
        raise OSError("fixture spawn refusal")

    monkeypatch.setattr(hmasd_launch, "_spawn", refuse_spawn)
    with pytest.raises(hmasd_launch.LaunchRefusal, match="cannot start admitted runner"):
        hmasd_launch.launch(args)
    monkeypatch.setattr(
        hmasd_launch,
        "_prepare_paths_and_config",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("existing operation reached new-effect gates")
        ),
    )

    recovered = hmasd_launch.launch(args)
    assert recovered["request_resolution"] == "existing_operation"
    assert recovered["admission"]["claim_state"] == "spawn_failed"
    assert recovered["execution"]["state"] == "not_started"
    assert recovered["explicit_retry_available"] is False


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


def test_pause_change_during_memory_assessment_is_denied_before_grant(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    real_assess = hmasd_launch.hmasd_resource_preflight.assess_memory_floor

    def assess_then_pause(snapshot):
        result = real_assess(snapshot)
        (source / "docs" / "research" / "RESEARCH.md").write_text(
            _research(pause="in force"), encoding="utf-8"
        )
        return result

    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "assess_memory_floor",
        assess_then_pause,
    )
    args = _arguments(source, sha, "pause-final-window")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="control authority changed|pause"):
        hmasd_launch.launch(args)
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
    first_manifest = hmasd_launch.launch(first)
    _wait_for(Path(first.output) / "summary.json")
    second = _arguments(source, sha, "renamed-output")
    recovered = hmasd_launch.launch(second)
    assert recovered["request_resolution"] == "existing_operation"
    assert recovered["operation_ref"] == first_manifest["operation_ref"]
    assert recovered["output_root"] == str(Path(first.output).resolve())
    assert not Path(second.output).exists()


def test_replay_and_status_do_not_consult_current_policy_or_source(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "lost-response")
    manifest = hmasd_launch.launch(args)
    output = Path(args.output)
    _wait_for(output / "process-exit.json")

    (source / "docs" / "research" / "RESEARCH.md").write_text(
        _research(pause="in force"), encoding="utf-8"
    )
    runner = source / "scripts" / "fixture_runner.py"
    runner.write_text(runner.read_text(encoding="utf-8") + "\n# author edit\n", encoding="utf-8")
    monkeypatch.setattr(
        hmasd_launch,
        "_prepare_paths_and_config",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("existing operation reached new-effect gates")
        ),
    )

    observed = hmasd_launch.status(output)
    replayed = hmasd_launch.launch(args)
    assert observed["execution"]["state"] == "exited"
    assert observed["execution"]["exit_code"] == 0
    assert observed["operation_ref"] == manifest["operation_ref"]
    assert replayed["request_resolution"] == "existing_operation"
    assert replayed["operation_ref"] == manifest["operation_ref"]
    assert hmasd_launch.status(manifest["manifest_ref"])["operation_ref"] == manifest[
        "operation_ref"
    ]
    assert hmasd_launch.status(manifest["operation_ref"])["manifest_ref"] == manifest[
        "manifest_ref"
    ]


def test_same_output_with_changed_input_reports_the_difference(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "immutable-request")
    hmasd_launch.launch(args)
    _wait_for(Path(args.output) / "process-exit.json")
    changed = _arguments(source, sha, "immutable-request")
    changed.runner_argv.extend(["--seed", "2"])
    with pytest.raises(hmasd_launch.LaunchRefusal, match="input mismatch.*runner_argv"):
        hmasd_launch.launch(changed)


def test_status_keeps_missing_or_mismatched_exit_uncertain(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "witness-validation")
    manifest = hmasd_launch.launch(args)
    output = Path(args.output)
    witness_path = output / "process-exit.json"
    _wait_for(witness_path)
    witness = json.loads(witness_path.read_text(encoding="utf-8"))
    witness["process_identity"] = {**witness["process_identity"], "pid": 999999}
    witness_path.write_text(json.dumps(witness), encoding="utf-8")

    mismatched = hmasd_launch.status(manifest["manifest_ref"])
    assert mismatched["execution"]["state"] == "unknown"
    assert mismatched["execution"]["exit_witness"]["state"] == "invalid"
    assert "runner_identity" in mismatched["execution"]["exit_witness"]["mismatches"]
    assert "exit_code" not in mismatched["execution"]

    witness_path.unlink()
    missing = hmasd_launch.status(manifest["operation_ref"])
    assert missing["execution"]["state"] == "unknown"
    assert missing["execution"]["exit_witness"]["state"] == "absent"
    assert missing["execution"]["runner"]["state"] in {"absent", "not_running"}
    assert "exit_code" not in missing["execution"]


def test_status_follows_runner_when_supervisor_and_runner_diverge(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "divergent-processes")
    manifest = hmasd_launch.launch(args)
    output = Path(args.output)
    _wait_for(output / "process-exit.json")
    (output / "process-exit.json").unlink()
    runner_identity = manifest["runner_process"]["identity"]

    def observe(recorded):
        if recorded == runner_identity:
            return {"state": "running", "recorded_identity": dict(recorded)}
        return {"state": "identity_mismatch", "recorded_identity": dict(recorded)}

    monkeypatch.setattr(hmasd_launch, "_observe_native_identity", observe)
    observed = hmasd_launch.status(manifest["manifest_ref"])
    assert observed["execution"]["state"] == "running"
    assert observed["execution"]["supervisor"]["state"] == "identity_mismatch"
    assert observed["execution"]["runner"]["state"] == "running"


def test_status_refuses_local_pid_probe_for_another_host_and_live_exit_conflict(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "host-bound")
    manifest = hmasd_launch.launch(args)
    output = Path(args.output)
    _wait_for(output / "process-exit.json")
    manifest_path = Path(manifest["manifest_ref"])
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored["host_identity"] = "definitely-another-host"
    manifest_path.write_text(json.dumps(stored), encoding="utf-8")

    remote_observation = hmasd_launch.status(manifest_path)
    assert remote_observation["execution"]["runner"]["state"] == "unavailable"
    assert remote_observation["execution"]["state"] == "exited"

    stored["host_identity"] = hmasd_launch.platform.node()
    manifest_path.write_text(json.dumps(stored), encoding="utf-8")
    monkeypatch.setattr(
        hmasd_launch,
        "_observe_native_identity",
        lambda recorded: {"state": "running", "recorded_identity": dict(recorded)},
    )
    conflicted = hmasd_launch.status(manifest_path)
    assert conflicted["execution"]["state"] == "unknown"
    assert "exit_code" not in conflicted["execution"]
    assert "live with exit witness" in conflicted["execution"]["conflict"]


def test_status_exposes_claim_manifest_identity_conflict(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    args = _arguments(source, sha, "record-conflict")
    manifest = hmasd_launch.launch(args)
    _wait_for(Path(args.output) / "process-exit.json")
    claim_path = Path(manifest["operation_ref"])
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim["sha"] = "0" * 40
    claim_path.write_text(json.dumps(claim), encoding="utf-8")

    observed = hmasd_launch.status(manifest["manifest_ref"])
    assert observed["record_consistency"] == {"state": "conflict", "mismatches": ["sha"]}
    assert observed["admission"]["state"] == "unknown"
    assert observed["execution"]["state"] == "unknown"
    assert "exit_code" not in observed["execution"]


def test_concurrent_identical_requests_spawn_once(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    real_spawn = hmasd_launch._spawn
    spawn_count = 0

    def counted_spawn(*args, **kwargs):
        nonlocal spawn_count
        spawn_count += 1
        return real_spawn(*args, **kwargs)

    monkeypatch.setattr(hmasd_launch, "_spawn", counted_spawn)
    first = _arguments(source, sha, "concurrent")
    second = _arguments(source, sha, "concurrent")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(hmasd_launch.launch, (first, second)))
    assert spawn_count == 1
    assert sum(result.get("request_resolution") == "existing_operation" for result in results) == 1
    assert len({result["operation_ref"] for result in results}) == 1


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
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
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


def test_configured_path_prefix_reaches_the_child_environment(monkeypatch) -> None:
    monkeypatch.setenv("PATH", "/inherited/bin")
    monkeypatch.setenv("PYTHONPATH", "/author/edits")
    prefix = os.pathsep.join(["/node/venv/bin", "/node/local/bin"])

    plain = hmasd_launch._child_environment({"path_prefix": prefix}, snapshot=False)
    assert plain["PATH"] == prefix + os.pathsep + "/inherited/bin"
    assert plain["PYTHONPATH"] == "/author/edits"

    snapshot = hmasd_launch._child_environment({"path_prefix": prefix}, snapshot=True)
    assert snapshot["PATH"] == prefix + os.pathsep + "/inherited/bin"
    assert "PYTHONPATH" not in snapshot

    assert hmasd_launch._child_environment({}, snapshot=False)["PATH"] == "/inherited/bin"
    monkeypatch.delenv("PATH")
    assert hmasd_launch._child_environment({"path_prefix": prefix}, snapshot=False)["PATH"] == prefix


@pytest.mark.parametrize("value", ["", "   ", 7, ["/node/venv/bin"]])
def test_malformed_path_prefix_is_refused(value) -> None:
    with pytest.raises(hmasd_launch.LaunchRefusal, match="path_prefix"):
        hmasd_launch._configured_path_prefix({"path_prefix": value})


def test_malformed_path_prefix_refuses_before_any_effect(
    launch_repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _remote, _sha = launch_repo
    monkeypatch.setattr(
        hmasd_launch.hmasd_resource_preflight,
        "capture_snapshot",
        lambda: SAFE_SNAPSHOT,
    )
    config = source / ".codex" / "hmasd-compute.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(
        text.replace(f'path_prefix = "{source.resolve().as_posix()}/node-bin"', "path_prefix = 7"),
        encoding="utf-8",
    )
    _git(source, "commit", "-am", "malformed prefix")
    _git(source, "push", "origin", "main")
    sha = _git(source, "rev-parse", "HEAD").stdout.strip()
    args = _arguments(source, sha, tag="malformed-prefix")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="path_prefix"):
        hmasd_launch.launch(args)
    assert not Path(args.output).exists()


def test_control_plane_node_is_selected_by_platform_then_fallback(monkeypatch) -> None:
    monkeypatch.delenv(hmasd_launch.CONTROL_PLANE_NODE_ENV, raising=False)
    nodes = {"win": {}, "lin": {}, "legacy": {}, "remote": {}}
    config = {
        "control_plane_node": "legacy",
        "control_plane_by_platform": {"win32": "win", "linux": "lin"},
        "nodes": nodes,
    }
    monkeypatch.setattr(hmasd_launch.sys, "platform", "linux")
    assert hmasd_launch._node_config(config, None)[0] == "lin"
    monkeypatch.setattr(hmasd_launch.sys, "platform", "win32")
    assert hmasd_launch._node_config(config, None)[0] == "win"
    monkeypatch.setattr(hmasd_launch.sys, "platform", "darwin")
    assert hmasd_launch._node_config(config, None)[0] == "legacy"
    # An explicit request and the environment override both outrank the table.
    assert hmasd_launch._node_config(config, "remote")[0] == "remote"
    monkeypatch.setenv(hmasd_launch.CONTROL_PLANE_NODE_ENV, "remote")
    assert hmasd_launch._node_config(config, None)[0] == "remote"
    monkeypatch.setenv(hmasd_launch.CONTROL_PLANE_NODE_ENV, "absent")
    with pytest.raises(hmasd_launch.LaunchRefusal, match="not configured"):
        hmasd_launch._node_config(config, None)


@pytest.mark.parametrize("table", ["local_linux", {"linux": 7}, {"linux": ""}])
def test_malformed_platform_table_is_refused(table, monkeypatch) -> None:
    monkeypatch.delenv(hmasd_launch.CONTROL_PLANE_NODE_ENV, raising=False)
    with pytest.raises(hmasd_launch.LaunchRefusal, match="control_plane_by_platform"):
        hmasd_launch._node_config({"control_plane_by_platform": table, "nodes": {}}, None)


def test_tracked_compute_file_names_a_configured_node_for_each_platform() -> None:
    config = hmasd_launch._load_config(ROOT / ".codex" / "hmasd-compute.toml")
    table = config["control_plane_by_platform"]
    assert set(table) == {"win32", "linux"}
    for node in table.values():
        assert config["nodes"][node]["role"].startswith("control_plane")
