"""Host-only task definitions. Never copy this directory into candidate workspaces."""
from pathlib import Path
from .catalog import TASKS, SOURCES, REFERENCES


def install(workspace: Path, task_id: str):
    """Install just one task; disjoint package names permit a two-task episode."""
    workspace = Path(workspace)
    for relative, contents in SOURCES[task_id].items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def apply_reference(workspace: Path, task_id: str):
    """Calibration only: replace owned source files, never public checks or brief."""
    for relative, contents in REFERENCES[task_id].items():
        assert relative in TASKS[task_id]["owned_paths"]
        (Path(workspace) / relative).write_text(contents, encoding="utf-8")


def grade(workspace: Path, task_id: str, interpreter=None):
    from .grade import grade as run
    return run(workspace, task_id, interpreter)
