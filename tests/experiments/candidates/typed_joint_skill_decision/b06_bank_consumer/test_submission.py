"""Use the actual installed supervisor template with harmless local markers."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer.submission import agent_task_argv


FIXTURE = Path(__file__).parent / "fixtures/agent-task.sh"
INSTALLED_SHA = "a7b8c1ff1691e11527cadf6adc677fd2caf00efe1bc0185ada524a5467455553"


def wrapper(tmp_path, command_arguments):
    source = FIXTURE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == INSTALLED_SHA
    source = source.decode()
    assignment = '        COMMAND="$*"'
    assert source.count(assignment) == 1
    start = '        cat <<EOF > "${WRAPPER}"\n'
    assert source.count(start) == 1
    body = source.split(start, 1)[1].split('\nEOF\n', 1)[0]
    assert 'eval ${COMMAND@Q}' in body
    task = tmp_path / "supervisor"
    task.mkdir()
    variables = {"NAME": "fixed-bank-test", "WRAPPER": str(task / "runner.sh"),
                 "LOG_FILE": str(task / "task.log"), "PID_FILE": str(task / "pid"),
                 "STATUS_FILE": str(task / "status"), "EXIT_FILE": str(task / "exit_code")}
    (task / "status").write_text("running\n")
    generator = assignment.strip() + "\n" + "\n".join(
        key + "=" + shlex.quote(value) for key, value in variables.items())
    generator += '\ncat <<EOF > "${WRAPPER}"\n' + body + '\nEOF\n'
    subprocess.run(["bash", "-c", generator, "generate", *command_arguments], check=True)
    return task


def marker_case(tmp_path, exit_code):
    repository = tmp_path / "repo with 'quote"
    (repository / "scripts").mkdir(parents=True)
    launcher = repository / "scripts/hmasd_launch.py"
    result = tmp_path / "observed.json"
    launcher.write_text(
        "import json,os,pathlib,sys\n"
        "pathlib.Path(sys.argv[2]).write_text(json.dumps({'cwd':os.getcwd(),'argv':sys.argv[1:]}))\n"
        "raise SystemExit(int(sys.argv[3]))\n")
    argv = [sys.executable, "-B", str(launcher), "launch", str(result), str(exit_code),
            "--lead", "Codex DM (native child)", "literal 'quotes' ; $(not_a_command)"]
    submitted = agent_task_argv("fixed-bank-test", str(repository), argv)
    assert len(submitted) == 4
    assert shlex.split(submitted[3])[:2] == ["zsh", "-lic"]
    # Isolate personal zsh startup files. This exercises parsing, not runtime health.
    zdot = tmp_path / "zdot"
    zdot.mkdir()
    wrong_start = tmp_path / "wrong-start"
    wrong_start.mkdir()
    environment = dict(os.environ, ZDOTDIR=str(zdot))
    return repository, result, argv, submitted, wrong_start, environment


@pytest.mark.parametrize("exit_code", [0, 37])
def test_single_command_preserves_cwd_argv_and_supervisor_exit(tmp_path, exit_code):
    repo, result, argv, submitted, wrong_start, environment = marker_case(tmp_path, exit_code)
    task = wrapper(tmp_path, submitted[3:])
    # The actual wrapper runs only the marker, never hmasd_launch or agent-task.
    process = subprocess.run(["bash", str(task / "runner.sh")], cwd=wrong_start, env=environment)
    assert process.returncode == 0
    assert json.loads(result.read_text()) == {"cwd": str(repo), "argv": argv[3:]}
    assert int((task / "exit_code").read_text()) == exit_code
    assert (task / "status").read_text().strip() == ("finished" if exit_code == 0 else "failed")
    assert "exited with code " + str(exit_code) in (task / "task.log").read_text()


def test_old_split_arguments_reproduce_wrong_cwd_and_missing_exit(tmp_path):
    repo, result, argv, submitted, wrong_start, environment = marker_case(tmp_path, 37)
    # This is the old request's three arguments before installed COMMAND="$*".
    task = wrapper(tmp_path, shlex.split(submitted[3]))
    process = subprocess.run(["bash", str(task / "runner.sh")], cwd=wrong_start, env=environment)
    assert process.returncode == 37
    assert json.loads(result.read_text()) == {"cwd": str(wrong_start), "argv": argv[3:]}
    assert not (task / "exit_code").exists()
    assert (task / "status").read_text() == "running\n"


def test_relative_native_launcher_refused_before_submission():
    with pytest.raises(ValueError, match="absolute interpreter/repository/native launcher"):
        agent_task_argv("fixed-bank-test", "/home/wu/projects/HMASD",
                        [sys.executable, "-B", "scripts/hmasd_launch.py", "launch"])
