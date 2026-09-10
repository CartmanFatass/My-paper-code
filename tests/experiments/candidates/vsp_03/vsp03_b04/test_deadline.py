"""Linux-only harmless lifecycle checks; never import the scientific implementation."""
import argparse
import json
import os
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import time


def process_state(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        return None


def check_case(adapter, scratch, name, mode):
    case = scratch / name
    case.mkdir()
    pids = case / "pids.json"
    ready = case / "ready"
    terminal = case / "terminal.json"
    # A root, child and grandchild all keep the adapter's process group. The root
    # waits for the tree to exist before exiting7, sleeping, or stopping the adapter.
    leaf = "import time; time.sleep(60)"
    branch = (
        "import subprocess,sys,time,pathlib; "
        f"p=subprocess.Popen([sys.executable,'-c',{leaf!r}]); "
        f"pathlib.Path({str(ready)!r}).write_text(str(p.pid)); time.sleep(60)"
    )
    root = (
        "import json,os,pathlib,signal,subprocess,sys,time\n"
        f"p=subprocess.Popen([sys.executable,'-c',{branch!r}])\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        "while not ready.exists(): time.sleep(.005)\n"
        f"pathlib.Path({str(pids)!r}).write_text(json.dumps({{'root':os.getpid(),"
        "'child':p.pid,'grandchild':int(ready.read_text()),'adapter':os.getppid()}))\n"
        + ("sys.exit(7)\n" if mode == "nonzero" else
           "os.kill(os.getppid(),signal.SIGSTOP)\ntime.sleep(60)\n" if mode == "hard" else
           "time.sleep(60)\n")
    )
    start = int(time.time())
    (case / "start_time").write_text(str(start) + "\n")
    cap, reserve = 7, 3
    command = ["bash", str(adapter), str(case / "start_time"), str(cap),
               str(reserve), str(terminal), "--", sys.executable, "-c", root]
    env = dict(os.environ, HMASD_PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE="1")
    result = {"name": name, "mode": mode, "start_time": start, "cap_s": cap,
              "reserve_s": reserve, "command": command}
    try:
        completed = subprocess.run(command, env=env, text=True, capture_output=True,
                                   timeout=cap + 5)
        result.update(shell_returncode=completed.returncode, stdout=completed.stdout,
                      stderr=completed.stderr, observed_finish_unix=time.time())
        result["origin_to_return_s"] = result["observed_finish_unix"] - start
        ids = json.loads(pids.read_text())
        # Allow init a short chance to reap hard-killed orphans. Zombies are
        # terminated processes, recorded distinctly rather than called absent.
        for _ in range(100):
            states = {role: process_state(pid) for role, pid in ids.items()}
            if all(state in (None, "Z") for state in states.values()):
                break
            time.sleep(.01)
        result.update(pids=ids, process_states_after_return=states)
        if terminal.exists():
            result["terminal"] = json.loads(terminal.read_text())
            result["terminal_mtime_unix_ns"] = terminal.stat().st_mtime_ns
        assert all(state in (None, "Z") for state in states.values()), states
        assert result["origin_to_return_s"] <= cap, result["origin_to_return_s"]
        if mode == "hard":
            assert completed.returncode == 137, completed.returncode
            assert "terminal" not in result, result.get("terminal")
        else:
            expected = 7 if mode == "nonzero" else 124
            record = result["terminal"]
            assert completed.returncode == expected, completed.returncode
            assert record["task_exit_code"] == expected, record
            assert record["timed_out"] == (mode == "timeout"), record
            assert record["root_returncode"] == (7 if mode == "nonzero" else -9), record
            assert record["all_descendants_terminated"] and not record["descendants_remaining"]
            assert record["error"] is None, record
            assert {ids["child"], ids["grandchild"]}.issubset(
                {row["pid"] for row in record["descendants_reaped"]}), record
            assert all(state is None for state in states.values()), states
            assert result["terminal_mtime_unix_ns"] / 1e9 - start <= cap
            printed = [json.loads(line) for line in completed.stdout.splitlines()
                       if line.startswith('{"terminal_published"')]
            assert len(printed) == 1 and printed[0]["task_exit_code"] == expected
            assert printed[0]["elapsed_through_terminal_readback_s"] <= cap
        result["passed"] = True
    except Exception as exc:
        result.update(passed=False, error=repr(exc))
    finally:
        # Only this fixture's recorded processes, never a scientific run. Retain
        # pre-cleanup states above so emergency test cleanup cannot conceal failure.
        if pids.exists():
            for pid in json.loads(pids.read_text()).values():
                if process_state(pid) not in (None, "Z"):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
    return result


def check_unit_case(source_root, scratch, name, mode):
    case = scratch / name
    case.mkdir()
    unit = f"vsp03-b04-review-{scratch.name}-{name}"
    task_dir = case / "tasks"
    record = case / "t.json"
    gate_pid = case / "controller.pid"
    pids_file = case / "pids.json"
    ready = case / "ready"
    metadata = case / "environment.json"
    installed = Path("/usr/local/bin/agent-task").read_text()
    original_line = 'TASK_DIR="${HOME}/.agent-tasks"'
    assert installed.count(original_line) == 1
    supervisor = case / "supervisor"
    supervisor.write_text(installed.replace(original_line, f'TASK_DIR="{task_dir}"'))
    supervisor.chmod(0o700)
    # Exact launch.sh emits its actual systemd-run argv. This test-only interceptor
    # records that argv, adds the existing controller's explicit fixture paths, and
    # inserts an ExecStart fault gate before exec of the exact controller bytes.
    gate = case / "gate.py"
    gate.write_text(
        "import os,pathlib,subprocess,sys,time\n"
        f"pathlib.Path({str(gate_pid)!r}).write_text(str(os.getpid()))\n"
        + (f"p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
           f"pathlib.Path({str(pids_file)!r}).write_text(__import__('json').dumps({{'startup_child':p.pid}}))\n"
           "time.sleep(60)\n" if mode == "startup" else "")
        + "os.execv(sys.argv[1],sys.argv[1:])\n")
    interceptor = case / "systemd-run"
    interceptor.write_text(
        f"#!{sys.executable}\nimport json,os,pathlib,sys\n"
        "args=sys.argv[1:]\n"
        f"pathlib.Path({str(case / 'launch_argv.json')!r}).write_text(json.dumps(args))\n"
        f"at=args.index({sys.executable!r}); cmd=args[at:]; before=cmd.index('--')\n"
        f"cmd[before:before]=['--supervisor',{str(supervisor)!r},'--task-dir',{str(task_dir)!r}]\n"
        f"os.execv('/usr/bin/systemd-run',['/usr/bin/systemd-run',*args[:at],{sys.executable!r},{str(gate)!r},*cmd])\n")
    interceptor.chmod(0o700)
    leaf = "import time; time.sleep(60)"
    branch = (
        "import subprocess,sys,time,pathlib; "
        f"p=subprocess.Popen([sys.executable,'-c',{leaf!r}]); "
        f"pathlib.Path({str(ready)!r}).write_text(str(p.pid)); time.sleep(60)"
    )
    root = (
        "import json,os,pathlib,signal,subprocess,sys,time\n"
        f"p=subprocess.Popen([sys.executable,'-c',{branch!r}])\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        "while not ready.exists(): time.sleep(.005)\n"
        f"pathlib.Path({str(pids_file)!r}).write_text(json.dumps({{'root':os.getpid(),"
        "'child':p.pid,'grandchild':int(ready.read_text()),'payload_adapter':os.getppid()}))\n"
        f"pathlib.Path({str(metadata)!r}).write_text(json.dumps({{k:os.environ.get(k) for k in "
        "('VSP03_B04_COMMAND','VSP03_B04_STARTED','TMUX_TMPDIR')}))\n"
        + ("time.sleep(.2)\nsys.exit(7)\n" if mode == "nonzero" else
           f"os.kill(int(pathlib.Path({str(gate_pid)!r}).read_text()),signal.SIGSTOP)\ntime.sleep(60)\n"
           if mode == "stopped" else "time.sleep(60)\n")
    )
    cap, reserve = 10, 4
    command = ["bash", str(source_root / "experiments/candidates/vsp_03/vsp03_b04/launch.sh"),
               unit, str(source_root), name, str(record), str(cap), str(reserve),
               "--", sys.executable, "-c", root]
    env = dict(os.environ, PATH=str(case) + os.pathsep + os.environ["PATH"])
    result = {"name": name, "mode": mode, "unit": unit + ".service", "cap_s": cap,
              "reserve_s": reserve, "command": command, "supervisor_source": installed,
              "supervisor_fixture_change": {"from": original_line, "to": f'TASK_DIR="{task_dir}"'}}
    if mode == "precedence":
        # An interface fixture for publication-before-exit: retain literal earlier
        # payload0, but obtain the later7 from a real harmless shell invocation.
        stub = (
            f"#!{sys.executable}\nimport json,os,pathlib,subprocess,time\n"
            f"pathlib.Path({str(pids_file)!r}).write_text(json.dumps({{'supervisor_stub':os.getpid()}}))\n"
            f"pathlib.Path({str(record.with_suffix('.payload.json'))!r}).write_text(json.dumps({{'task_exit_code':0}}))\n"
            "time.sleep(.2)\n"
            "code=subprocess.run(['bash','-c','exit 7']).returncode\n"
            f"out=pathlib.Path({str(task_dir / name / 'exit_code')!r}); out.parent.mkdir(parents=True)\n"
            "out.write_text(str(code))\n")
        supervisor.write_text(stub)
        result["supervisor_fixture_change"] = "Literal earlier payload0 and real later shell exit7 stub; no tmux"
        result["supervisor_stub_source"] = stub
    proc = None
    cgroup = None
    ids = {}
    try:
        proc = subprocess.Popen(command, env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        for _ in range(400):
            if pids_file.exists() or proc.poll() is not None:
                break
            time.sleep(.01)
        props = subprocess.check_output([
            "systemctl", "--user", "show", unit + ".service", "-p", "ControlGroup",
            "-p", "InactiveExitTimestampMonotonic", "-p", "TimeoutStartUSec",
            "-p", "Type", "-p", "KillMode", "-p", "TimeoutStartFailureMode"], text=True)
        result["live_manager_properties"] = dict(line.split("=", 1) for line in props.splitlines())
        group_name = result["live_manager_properties"].get("ControlGroup", "")
        if group_name:
            cgroup = Path("/sys/fs/cgroup") / group_name.lstrip("/") / "cgroup.procs"
            result["contained_pids"] = [int(p) for p in cgroup.read_text().split()] if cgroup.exists() else []
        stdout, stderr = proc.communicate(timeout=cap + 4)
        finished = time.monotonic()
        result.update(client_returncode=proc.returncode, stdout=stdout, stderr=stderr,
                      finished_monotonic=finished)
        ids = json.loads(pids_file.read_text()) if pids_file.exists() else {}
        if gate_pid.exists():
            ids["controller_or_startup_gate"] = int(gate_pid.read_text())
        for pid in result.get("contained_pids", []):
            ids.setdefault(f"cgroup_{pid}", pid)
        result["pids"] = ids
        result["process_states_after_return"] = {role: process_state(pid) for role, pid in ids.items()}
        result["cgroup_pids_after_return"] = cgroup.read_text().split() if cgroup and cgroup.exists() else []
        final = subprocess.run(["systemctl", "--user", "show", unit + ".service",
            "-p", "Result", "-p", "ExecMainCode", "-p", "ExecMainStatus",
            "-p", "ExecMainExitTimestampMonotonic", "-p", "InactiveExitTimestampMonotonic",
            "-p", "ActiveState", "-p", "SubState"], text=True, capture_output=True)
        result["final_manager_properties"] = dict(line.split("=", 1) for line in final.stdout.splitlines())
        result["journal"] = subprocess.run(["journalctl", "--user", "-u", unit + ".service",
            "--no-pager", "-o", "short-monotonic"], text=True, capture_output=True).stdout
        result["actual_launch_argv"] = json.loads((case / "launch_argv.json").read_text())
        for filename in ("exit_code", "status", "task.log", "runner.sh"):
            path = task_dir / name / filename
            if path.exists():
                result["supervisor_" + filename] = path.read_text()
        if record.exists():
            result["terminal"] = json.loads(record.read_text())
        if metadata.exists():
            result["environment"] = json.loads(metadata.read_text())
        live = result["live_manager_properties"]
        started = int(live["InactiveExitTimestampMonotonic"]) / 1e6
        result["origin_to_return_s"] = finished - started
        assert live["Type"] == "oneshot" and live["KillMode"] == "control-group", live
        assert live["TimeoutStartFailureMode"] == "kill" and live["TimeoutStartUSec"] == "9s", live
        assert result["origin_to_return_s"] <= cap, result["origin_to_return_s"]
        assert not result["cgroup_pids_after_return"], result["cgroup_pids_after_return"]
        assert ids and all(state is None for state in result["process_states_after_return"].values())
        if mode in ("startup", "stopped"):
            assert "terminal" not in result, result.get("terminal")
            assert result["final_manager_properties"]["Result"] == "timeout"
            assert result["final_manager_properties"]["ExecMainStatus"] == "9"
        elif mode == "precedence":
            terminal = result["terminal"]
            assert terminal["payload"]["task_exit_code"] == 0
            assert terminal["supervisor_exit_code"] == terminal["task_exit_code"] == 7
            assert terminal["error"] is None and terminal["all_descendants_terminated"]
        else:
            expected = 7 if mode == "nonzero" else 124
            terminal = result["terminal"]
            assert terminal["task_exit_code"] == expected and terminal["supervisor_exit_code"] == expected
            assert terminal["all_descendants_terminated"] and not terminal["descendants_remaining"]
            assert terminal["error"] is None
            assert terminal["payload"]["task_exit_code"] == expected
            assert terminal["started_monotonic"] == terminal["payload"]["started_monotonic"] == started
            assert terminal["elapsed_before_terminal_publication_s"] <= cap
        if mode not in ("startup", "precedence"):
            assert result["environment"]["VSP03_B04_COMMAND"] == shlex.join([sys.executable, "-c", root])
            assert float(result["environment"]["VSP03_B04_STARTED"]) == started
            assert result["environment"]["TMUX_TMPDIR"] == str(record.with_suffix(".tmux"))
        result["passed"] = True
    except Exception as exc:
        result.update(passed=False, error=repr(exc))
    finally:
        # Only this named test unit; record pre-cleanup observations first.
        subprocess.run(["systemctl", "--user", "stop", unit + ".service"], capture_output=True)
        subprocess.run(["systemctl", "--user", "reset-failed", unit + ".service"], capture_output=True)
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.communicate()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--unit-source", type=Path)
    args = parser.parse_args()
    if args.unit_source:
        results = [check_unit_case(args.unit_source, args.scratch, name, mode) for name, mode in (
            ("n", "nonzero"), ("w", "timeout"), ("s", "startup"), ("k", "stopped"),
            ("p", "precedence"))]
    else:
        results = [check_case(args.adapter, args.scratch, name, mode) for name, mode in (
            ("normal_nonzero_orphans", "nonzero"), ("work_timeout_tree", "timeout"),
            ("hard_containment_stopped_adapter", "hard"))]
    print(json.dumps({"checks": results, "passed": all(r["passed"] for r in results),
                      "scientific_models_episodes_updates": [0, 0, 0]}, indent=2))
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
