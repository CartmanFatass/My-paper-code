import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from experiments.candidates.capability_bound_semantic_currentness.local_acquisition_p16 import inputs, local
from experiments.candidates.capability_bound_semantic_currentness.local_acquisition_p16.processes import WindowsJob

ROOT = Path(__file__).resolve().parents[5]
HERE = ROOT / "experiments/candidates/capability_bound_semantic_currentness/local_acquisition_p16"
RUNNER = ROOT / "scripts/run_cbsc_local_acquisition_p16.py"


def load_remote(monkeypatch):
    monkeypatch.syspath_prepend(str(HERE))
    spec = importlib.util.spec_from_file_location("p16_remote_test", HERE / "remote.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def args(out):
    return SimpleNamespace(out=str(out), source="a" * 40, seed=0, handle="p16-fixture",
                           remote_python="/usr/bin/python3", remote_repo="/fixture/source",
                           remote_out="/fixture/out", candidate="/fixture/candidate",
                           retained="/fixture/retained", uv="/fixture/uv", supervisor="/fixture/agent-task",
                           ssh="fake-ssh", ssh_target="fake-node", powershell="fake-powershell", tmux="/fixture/tmux")


class FakeCalls:
    def __init__(self, fail=None, summary=None, remote_code=0, collection_elapsed=1):
        self.now = 100.0
        self.events = []
        self.fail = fail
        self.summary = {"metadata_matches": True, "fixture": True} if summary is None else summary
        self.remote_code, self.collection_elapsed = remote_code, collection_elapsed

    def clock(self):
        return self.now

    def admission(self):
        self.events.append("admission")
        self.now += 2

    def anchor(self):
        self.events.append("anchor")
        self.now += 2
        return {"seconds": 1000.0, "boot": "fixture-boot"}

    def download(self, body, target):
        self.events.append(body[0])
        self.now += 50
        target.write_bytes(b"x" * (body[2] - (self.fail == "partial")))

    def transfer(self, files, anchor, deadline):
        self.events.append("transfer")
        self.now += 30
        self.deadline = deadline
        if self.fail == "transfer":
            raise OSError("fixture transfer failure")

    def launch(self, anchor, deadline):
        self.events.append("launch")
        self.now += 20  # Dispatch and startup delay, never a new allowance.
        self.deadline = deadline
        if self.fail == "launch":
            raise OSError("fixture connection lost; acceptance unknown")

    def collect(self, anchor, deadline):
        self.events.append("collect")
        self.now += self.collection_elapsed
        return {"terminal": {"exit_code": self.remote_code},
                "summary": None if self.summary == "absent" else self.summary}


FIXTURE_BODIES = (("first.whl", "https://invalid/first", 3), ("second.whl", "https://invalid/second", 4))


def run_fake(tmp_path, calls):
    return local.chain(args(tmp_path / "out"), 100.0, calls, calls.clock, FIXTURE_BODIES)


def test_import_help_and_frozen_inputs(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("An external boundary was called by the inert path")
    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", forbidden)
        spec = importlib.util.spec_from_file_location("p16_runner_test", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with pytest.raises(SystemExit) as exc:
            module.main(["--help"])
        assert exc.value.code == 0
    doc = (ROOT / "docs/research/candidates/capability_bound_semantic_currentness/CBSC_POST_A03_ACQUISITION_ROOT_HANDOFF_20260907.md").read_text(encoding="utf-8")
    shell = shlex.split(doc.split("```sh\n")[1].split("\n```", 1)[0])[-1]
    link_program = shell.split("<<'PY_LINK'\n")[1].split("\nPY_LINK")[0]
    names = next(ast.literal_eval(node.iter) for node in ast.walk(ast.parse(link_program)) if isinstance(node, ast.For))
    assert tuple(names) == inputs.CONTAINERS and len(names) == 21
    install = next(line for line in shell.splitlines() if "--no-config pip install" in line)
    assert set(inputs.PINS) == {part for part in shlex.split(install) if "==" in part}
    assert len(inputs.PINS) == 23
    for name, url, size in inputs.BODIES:
        assert url in shell and name in shell and size in (955455844, 156503769)
    original_meta = shell.split("<<'PY_META'\n")[1].split("\nPY_META")[0]
    new_meta = (HERE / "metadata.py").read_text(encoding="utf-8")
    assert original_meta.split('result["metadata_matches"] = (')[1] == new_meta.split('result["metadata_matches"] = (')[1].rstrip("\n")
    assert new_meta.count("import numpy\n") == new_meta.count("import torch\n") == 1
    ps = (HERE / "download.ps1").read_text(encoding="utf-8")
    for literal in ("UseProxy = $false", "UseDefaultCredentials = $false", "Credentials = $null",
                    "UseCookies = $false", "AllowAutoRedirect = $false", "FileMode]::CreateNew"):
        assert literal in ps
    assert ps.count(".GetAsync(") == 1 and ".CopyTo(" in ps
    assert "ServerCertificate" not in ps and "Add('Range'" not in ps
    command = local.ssh_command(args(Path("fixture")), "receive", {"boot": "boot"}, 1500)
    words = shlex.split(command[-1])
    assert words[1] == "/fixture/source/experiments/candidates/capability_bound_semantic_currentness/local_acquisition_p16/remote.py"
    assert words[words.index("--deadline") + 1] == "1500"


def test_remaining_clock_mapping_charges_every_phase(tmp_path, monkeypatch):
    calls = FakeCalls()
    result = run_fake(tmp_path, calls)
    remote = load_remote(monkeypatch)
    assert result["ready"] and result["metadata_collected"]
    assert calls.events == ["admission", "anchor", "first.whl", "second.whl", "transfer", "launch", "collect"]
    assert calls.deadline == pytest.approx(1000 + (540 - 4 - 1) / 1.01)
    after_dispatch = 1000 + 150  # 100 download + 30 transfer + 20 dispatch/start.
    allowance = remote.remote_remaining(calls.deadline, "fixture-boot", {"boot": "fixture-boot", "seconds": after_dispatch})
    assert allowance < 390 and allowance != 540
    with pytest.raises(TimeoutError):
        remote.remote_remaining(calls.deadline, "fixture-boot", {"boot": "fixture-boot", "seconds": calls.deadline + 1})
    with pytest.raises(RuntimeError, match="clock domain"):
        remote.remote_remaining(calls.deadline, "fixture-boot", {"boot": "reboot", "seconds": 1})
    with pytest.raises(TimeoutError):
        local.map_deadline({"seconds": 1000}, 1)
    summary = json.loads((tmp_path / "out/summary.json").read_text())
    assert summary == {"metadata_matches": True, "fixture": True}
    assert result["whole_wall_seconds"] == 155


@pytest.mark.parametrize("failure", ["partial", "transfer", "launch"])
def test_failure_stops_next_phase_and_preserves_bytes(tmp_path, failure):
    original = tmp_path / "retained.whl"
    original.write_bytes(b"immutable fixture")
    calls = FakeCalls(fail=failure)
    result = run_fake(tmp_path, calls)
    assert not result["ready"] and not result["metadata_collected"]
    assert original.read_bytes() == b"immutable fixture"
    if failure == "partial":
        assert calls.events == ["admission", "anchor", "first.whl"]
        assert (tmp_path / "out/first.whl").read_bytes() == b"xx"
    elif failure == "transfer":
        assert "launch" not in calls.events
    else:
        assert "collect" not in calls.events and result["remote_acceptance"] == "uncertain"


@pytest.mark.parametrize("options", [{"remote_code": 1}, {"summary": "absent"},
                                      {"summary": {"metadata_matches": False}}, {"collection_elapsed": 601}])
def test_false_success_boundaries(tmp_path, options):
    result = run_fake(tmp_path, FakeCalls(**options))
    assert result["ready"] is False


def test_exhausted_local_time_starts_no_next_download(tmp_path):
    calls = FakeCalls()
    def admission():
        calls.events.append("admission")
        calls.now += 541
    calls.admission = admission
    result = run_fake(tmp_path, calls)
    assert not result["ready"] and calls.events == ["admission"]


def test_receiver_partial_and_complete_fixture(tmp_path, monkeypatch):
    remote = load_remote(monkeypatch)
    with pytest.raises(RuntimeError, match="Incomplete transfer"):
        remote.receive(tmp_path / "failed", io.BytesIO(b"xy"), FIXTURE_BODIES)
    assert (tmp_path / "failed/wheels/first.whl").read_bytes() == b"xy"
    assert not (tmp_path / "failed/wheels/second.whl").exists()
    remote.receive(tmp_path / "complete", io.BytesIO(b"1234567"), FIXTURE_BODIES)
    assert (tmp_path / "complete/wheels/second.whl").read_bytes() == b"4567"


@pytest.mark.parametrize("fail_install", [False, True])
def test_actual_setup_builder_uses_only_frozen_chain(tmp_path, monkeypatch, fail_install):
    remote = load_remote(monkeypatch)
    options = args(tmp_path / "out")
    options.python = options.remote_python
    options.repo = options.remote_repo
    options.candidate = str(tmp_path / "candidate")
    options.deadline, options.boot = 540, "fixture"
    monkeypatch.setattr(remote.os, "chdir", lambda path: None)
    monkeypatch.setattr(remote, "remote_remaining", lambda *a: 10)
    options.retained = str(tmp_path / "retained")
    Path(options.retained).mkdir()
    (Path(options.out) / "wheels").mkdir(parents=True)
    (Path(options.retained) / "sentinel").write_bytes(b"read-only fixture")
    links = []
    monkeypatch.setattr(Path, "symlink_to", lambda self, target: links.append((self, target)))
    calls = []
    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if "install" in command and fail_install:
            raise subprocess.CalledProcessError(1, command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(remote.subprocess, "run", fake_run)
    if fail_install:
        with pytest.raises(subprocess.CalledProcessError):
            remote.setup(options)
    else:
        remote.setup(options)
    assert len(calls) == (3 if fail_install else 4)
    assert calls[0][0][2] == "admit-memory"
    assert calls[1][0] == [options.uv, "--no-config", "venv", "--python", "/usr/bin/python3",
                           "--no-python-downloads", options.candidate]
    install = calls[2][0]
    assert tuple(install[-23:]) == inputs.PINS
    assert "--no-index" in install and ":all:" in install
    assert "--no-deps" not in install
    if not fail_install:
        assert calls[3][0][0] == str(Path(options.candidate) / "bin/python")
        assert calls[3][0][1] == str(HERE / "metadata.py")
        assert calls[3][0][-2:] == ["a" * 40, "0"]
    assert all(call[1]["env"]["OMP_NUM_THREADS"] == "1" for call in calls)
    assert {p.name for p, _ in links} == set(inputs.CONTAINERS)
    assert all(target.parent == Path(options.retained) for _, target in links)
    assert all(p.read_bytes() == b"read-only fixture" for p in Path(options.retained).iterdir())


def test_remote_expired_dispatch_starts_no_external_work(tmp_path, monkeypatch):
    remote = load_remote(monkeypatch)
    monkeypatch.setattr(remote, "clock_sample", lambda: {"boot": "same", "seconds": 101})
    def forbidden(*a, **kw):
        raise AssertionError("Late dispatch started external work")
    monkeypatch.setattr(remote, "LinuxLimit", forbidden)
    monkeypatch.setattr(remote.subprocess, "run", forbidden)
    with pytest.raises(TimeoutError):
        remote.main(["launch", "--deadline", "100", "--boot", "same"])


def test_scheduling_gap_cannot_restart_remote_clock(tmp_path, monkeypatch):
    remote = load_remote(monkeypatch)
    # The first clock sample is 100; scheduling resumes at 700. The old
    # BOOTTIME->monotonic conversion manufactured 700 + (540 - 100) = 1140.
    monkeypatch.setattr(remote, "clock_sample", lambda: {"boot": "same", "seconds": 100})
    monkeypatch.setattr(remote, "boottime", lambda: 700)
    observed = []
    class FakeAbsoluteLimit:
        def __init__(self, deadline):
            observed.append(deadline)
            if deadline <= remote.boottime():
                raise TimeoutError("absolute timer already expired")
        def run(self, *a, **kw):
            pytest.fail("Scheduling gap started a new phase")
    monkeypatch.setattr(remote, "LinuxLimit", FakeAbsoluteLimit)
    with pytest.raises(TimeoutError, match="already expired"):
        remote.main(["controller", "--deadline", "540", "--boot", "same"])
    assert observed == [599]  # Original 540 work cutoff + 59 publication margin.


PROCESS_FIXTURE = '''
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from experiments.candidates.capability_bound_semantic_currentness.local_acquisition_p16.processes import WindowsJob, remaining
mode, out = sys.argv[2], Path(sys.argv[3])
if mode == "branch":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    out.write_text(json.dumps({"branch": __import__("os").getpid(), "leaf": child.pid}))
    time.sleep(60)
else:
    # The fake remote's clock deadline is fixed before child bootstrap, just as
    # the production remote controller receives a fixed node-domain deadline.
    deadline = float(sys.argv[4]) if mode == "remote" else time.monotonic() + 60
    remaining(deadline)
    job = WindowsJob([sys.executable, __file__, sys.argv[1], "branch", str(out)])
    if mode == "before_resume":
        out.write_text(json.dumps({"suspended": job.pid}))
        time.sleep(60)
    job.resume()
    try:
        job.wait(remaining(deadline))
    except TimeoutError:
        pass
    finally:
        job.close()
'''


def await_file(path):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except ValueError:
                pass
        time.sleep(0.02)
    pytest.fail("Inert child did not publish its PIDs")


def assert_exited(pids):
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    for pid in pids.values():
        handle = k.OpenProcess(0x100000, False, pid)
        if handle:
            try:
                assert k.WaitForSingleObject(handle, 3000) == 0, f"inert descendant {pid} still live"
            finally:
                k.CloseHandle(handle)


@pytest.mark.skipif(os.name != "nt", reason="This contract's actual local boundary is Windows")
def test_actual_timeout_and_controller_loss_kill_descendants(tmp_path):
    fixture = tmp_path / "inert_process.py"
    fixture.write_text(PROCESS_FIXTURE)
    output = tmp_path / "timeout.json"
    job = WindowsJob([sys.executable, str(fixture), str(ROOT), "branch", str(output)])
    job.resume()
    try:
        pids = await_file(output)
        with pytest.raises(TimeoutError):
            job.wait(0.05)
    finally:
        job.close()
    assert_exited(pids)
    output = tmp_path / "controller_loss.json"
    controller = subprocess.Popen([sys.executable, str(fixture), str(ROOT), "controller", str(output)])
    try:
        pids = await_file(output)
        controller.kill()
        controller.wait(timeout=3)
        assert_exited(pids)
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait()


@pytest.mark.skipif(os.name != "nt", reason="Atomic Windows creation boundary")
def test_controller_loss_before_child_resume_is_contained(tmp_path):
    fixture = tmp_path / "inert_process.py"
    fixture.write_text(PROCESS_FIXTURE)
    output = tmp_path / "before_resume.json"
    controller = subprocess.Popen([sys.executable, str(fixture), str(ROOT), "before_resume", str(output)])
    try:
        pids = await_file(output)
        controller.kill()
        controller.wait(timeout=3)
        assert_exited(pids)
    finally:
        if controller.poll() is None:
            controller.kill()
        controller.wait()


@pytest.mark.skipif(os.name != "nt", reason="Inert remote controller fixture uses the available Windows OS")
def test_independent_fake_remote_deadline_survives_client_loss(tmp_path):
    fixture = tmp_path / "inert_process.py"
    fixture.write_text(PROCESS_FIXTURE)
    output = tmp_path / "remote.json"
    deadline = time.monotonic() + 1.8
    remote = subprocess.Popen([sys.executable, str(fixture), str(ROOT), "remote", str(output), str(deadline)])
    client = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        pids = await_file(output)
        client.kill()
        client.wait(timeout=3)
        assert remote.poll() is None  # No dependency on the now-dead client.
        assert remote.wait(timeout=4) == 0
        assert_exited(pids)
    finally:
        for process in (client, remote):
            if process.poll() is None:
                process.kill()
            process.wait()
