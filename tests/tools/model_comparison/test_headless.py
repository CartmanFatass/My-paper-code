from pathlib import Path
import importlib.util
import json
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


def test_resume_keeps_session_edits_and_accumulates_time(tmp_path):
    prompt = tmp_path / "feedback.md"
    prompt.write_bytes(b"Fix the reported defect under the original spec\n")
    for arm in module.MODELS:
        receipt = tmp_path / (arm + "-previous.json")
        target = str(tmp_path / "saved.jsonl") if arm == "omp" else "original-uuid"
        receipt.write_text(json.dumps({
            "arm": arm, "cwd": str(tmp_path), "source_sha": "base",
            "status": "exited", "exit_code": 0, "resume_target": target,
            "session_dir": str(tmp_path / "original-sessions"),
            "elapsed_seconds": 12, "cumulative_elapsed_seconds": 20, "turn_number": 2,
        }), encoding="utf-8")
        with patch.object(module.subprocess, "check_output", side_effect=["base\n", " M task.py\n"]), \
                patch.object(module.shutil, "which", return_value=arm), \
                patch.object(module.subprocess, "Popen") as popen:
            popen.return_value.pid = 123
            popen.return_value.returncode = 0
            result = module.run(arm, tmp_path, prompt, tmp_path / arm, "base", 60, receipt)
        argv = result["argv"]
        assert argv[argv.index("--resume") + 1] == target
        assert "--session-id" not in argv and "--fork-session" not in argv
        assert result["turn_number"] == 3 and not result["starting_worktree_clean"]
        assert result["cumulative_elapsed_seconds"] == 20 + result["elapsed_seconds"]
        assert result["previous_receipt"] == str(receipt.resolve())
        if arm == "omp":
            assert argv[argv.index("--session-dir") + 1] == str(tmp_path / "original-sessions")


def test_unknown_prior_execution_cannot_resume(tmp_path):
    prompt = tmp_path / "feedback.md"
    prompt.write_bytes(b"fix\n")
    receipt = tmp_path / "previous.json"
    receipt.write_text(json.dumps({"arm": "grok", "cwd": str(tmp_path), "source_sha": "base",
                                   "status": "termination_unconfirmed", "exit_code": None}), encoding="utf-8")
    with patch.object(module.subprocess, "check_output", side_effect=["base\n", ""]), \
            patch.object(module.subprocess, "Popen") as popen:
        import pytest
        with pytest.raises(ValueError, match="Resolve prior"):
            module.run("grok", tmp_path, prompt, tmp_path / "out", "base", 60, receipt)
        popen.assert_not_called()


def test_omp_records_exact_created_session_file(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"new task\n")
    output = tmp_path / "out"
    saved = output / "sessions" / "original.jsonl"

    def create_session(**kwargs):
        saved.parent.mkdir()
        saved.write_text('{"type":"session","id":"original"}\n', encoding="utf-8")

    with patch.object(module.subprocess, "check_output", side_effect=["base\n", "", ""]), \
            patch.object(module.shutil, "which", return_value="omp"), \
            patch.object(module.subprocess, "Popen") as popen:
        popen.return_value.pid = 123
        popen.return_value.returncode = 0
        popen.return_value.communicate.side_effect = create_session
        result = module.run("omp", tmp_path, prompt, output, "base", 60)
        assert result["resume_target"] == str(saved.resolve())


def test_empty_resume_receipt_never_starts_new_session(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"fix\n")
    receipt = tmp_path / "previous.json"
    receipt.write_text("{}", encoding="utf-8")
    with patch.object(module.subprocess, "check_output", side_effect=["base\n", ""]), \
            patch.object(module.subprocess, "Popen") as popen:
        import pytest
        with pytest.raises(ValueError, match="Missing session record"):
            module.run("grok", tmp_path, prompt, tmp_path / "out", "base", 60, receipt)
        popen.assert_not_called()
