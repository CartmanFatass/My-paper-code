from pathlib import Path
import importlib.util
from unittest.mock import patch


path = Path(__file__).resolve().parents[3] / "tools/model_comparison/run_headless.py"
spec = importlib.util.spec_from_file_location("cm_headless", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_explicit_models_efforts_and_no_interactive_modes():
    for arm, (exe, model, effort) in module.MODELS.items():
        cmd = module.command(arm, exe, Path("space dir"), Path("prompt.md"), Path("logs"), "id")
        assert cmd[cmd.index("--model") + 1] == model
        flag = {"claude": "--effort", "grok": "--reasoning-effort", "omp": "--thinking"}[arm]
        assert cmd[cmd.index(flag) + 1] == effort == "high"
        assert "--print" in cmd or "--prompt-file" in cmd
        assert "--resume" not in cmd and "--continue" not in cmd


def test_wrong_source_never_starts_provider(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"new task\n")
    with patch.object(module.subprocess, "check_output", side_effect=["wrong\n", "", "task.py\n"]), \
            patch.object(module.subprocess, "Popen") as popen:
        try:
            module.run("grok", tmp_path, prompt, tmp_path / "out", "expected", 60)
        except ValueError as error:
            assert "Wrong starting source" in str(error)
        else:
            raise AssertionError("Wrong baseline was accepted")
        popen.assert_not_called()


def test_claude_receives_exact_utf8_stdin_and_records_completion(tmp_path):
    prompt = tmp_path / "prompt.md"
    payload = "同一新任务\n".encode("utf-8")
    prompt.write_bytes(payload)
    with patch.object(module.subprocess, "check_output", side_effect=["equivalent-head\n", "", ""]), \
            patch.object(module.shutil, "which", return_value="claude.exe"), \
            patch.object(module.subprocess, "Popen") as popen:
        popen.return_value.pid = 123
        popen.return_value.returncode = 0
        result = module.run("claude", tmp_path, prompt, tmp_path / "out", "base", 60)
        popen.return_value.communicate.assert_called_once_with(input=payload, timeout=60)
        assert result["status"] == "exited" and result["exit_code"] == 0
        assert result["elapsed_seconds"] >= 0
        assert result["actual_head"] == "equivalent-head" and result["source_sha"] == "base"
        assert result["source_content_matches"]
        assert result["model_verification"] == "read_raw_session_before_acceptance"
        assert (tmp_path / "out/process.json").exists()


def test_dirty_start_never_starts_provider(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"same code spec\n")
    with patch.object(module.subprocess, "check_output", side_effect=["base\n", " M task.py\n"]), \
            patch.object(module.subprocess, "Popen") as popen:
        try:
            module.run("grok", tmp_path, prompt, tmp_path / "out", "base", 60)
        except ValueError as error:
            assert "starting modifications" in str(error)
        else:
            raise AssertionError("Dirty start was accepted")
        popen.assert_not_called()


def test_failed_timeout_termination_remains_unconfirmed(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"same code spec\n")
    with patch.object(module.subprocess, "check_output", side_effect=["base\n", "", ""]), \
            patch.object(module.shutil, "which", return_value="grok.exe"), \
            patch.object(module.subprocess, "Popen") as popen, \
            patch.object(module, "stop_process_tree", side_effect=RuntimeError("cannot stop PID 123")):
        popen.return_value.pid = 123
        popen.return_value.returncode = None
        popen.return_value.communicate.side_effect = module.subprocess.TimeoutExpired("grok", 60)
        result = module.run("grok", tmp_path, prompt, tmp_path / "out", "base", 60)
        assert result["status"] == "termination_unconfirmed"
        assert result["exit_code"] is None and result["pid"] == 123
        assert result["error"] == "cannot stop PID 123"
