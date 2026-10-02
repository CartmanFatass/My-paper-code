"""Render the installed WSL agent-task string interface; never submit a task."""
from __future__ import annotations

from pathlib import PurePosixPath
import shlex


def agent_task_argv(task_name, repository, native_argv):
    """Keep the entire child-shell command one argument through COMMAND="$*"."""
    argv = list(native_argv)
    if (not PurePosixPath(repository).is_absolute() or len(argv) < 4
            or not PurePosixPath(argv[0]).is_absolute() or argv[1] != "-B"
            or argv[2] != str(PurePosixPath(repository) / "scripts/hmasd_launch.py")
            or argv[3] != "launch"):
        raise ValueError("absolute interpreter/repository/native launcher command required")
    child = "cd -- " + shlex.quote(repository) + " && exec " + shlex.join(argv)
    command = shlex.join(["zsh", "-lic", child])
    return ["/usr/local/bin/agent-task", "run", task_name, command]
