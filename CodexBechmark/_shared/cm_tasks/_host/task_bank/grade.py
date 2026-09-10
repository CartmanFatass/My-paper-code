"""Host CLI: python -B grade.py --workspace PATH --task ID [OUTPUT.json]."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

if __package__:
    from .catalog import TASKS, HIDDEN
else:
    from catalog import TASKS, HIDDEN


def grade(workspace, task_id, interpreter=None):
    """One isolated worker; hidden assertions never import candidate public tests.

    interpreter defaults to the caller's Python; caller must supply the declared
    NumPy/torch environment (CLI --python can override). This is process isolation,
    not a security sandbox against hostile candidate code.
    """
    TASKS[task_id]
    workspace = Path(workspace).resolve()
    code = ("import sys, importlib\n"
            f"sys.path.insert(0, {str(workspace)!r})\n"
            f"api=importlib.import_module('cm_{task_id}.api')\n" + HIDDEN[task_id])
    try:
        result = subprocess.run([str(interpreter or sys.executable), "-I", "-B", "-c", code],
                                cwd=workspace, capture_output=True, text=True, timeout=30)
        check = dict(name="hidden_behavior", passed=result.returncode == 0,
                     returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
    except subprocess.TimeoutExpired:
        check = dict(name="hidden_behavior", passed=False, error="30 second check timeout")
    return dict(passed=check["passed"], checks=[check])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task", choices=TASKS, required=True)
    parser.add_argument("--python", dest="interpreter")
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    result = grade(args.workspace, args.task, args.interpreter)
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
