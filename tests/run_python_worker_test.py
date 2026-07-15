import json
import subprocess
import sys
from pathlib import Path


def test_python_worker_preserves_stderr_without_aborting(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stdout_path = tmp_path / "stdout.log"
    stderr_path = tmp_path / "stderr.log"
    exit_code_path = tmp_path / "exit_code.txt"
    spec_path = tmp_path / "worker_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "python_bin": sys.executable,
                "working_directory": str(repo_root),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "exit_code_path": str(exit_code_path),
                "arguments": [
                    "-c",
                    (
                        "import sys; "
                        "sys.stderr.write('sentinel-stderr\\n'); "
                        "print('sentinel-stdout')"
                    ),
                ],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_root / "scripts" / "run_python_worker.ps1"),
            "-SpecPath",
            str(spec_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert exit_code_path.read_text(encoding="utf-8") == "0"
    assert stdout_path.read_text(encoding="utf-16").strip() == "sentinel-stdout"
    stderr = stderr_path.read_text(encoding="utf-16")
    assert "sentinel-stderr" in stderr
    assert "worker_wrapper_error" not in stderr
