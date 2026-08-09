"""Proof-sized behavioral checks for the schema-v3 readiness executor."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import argparse
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / ".agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py"
MODULE_SPEC = importlib.util.spec_from_file_location("hmasd_readiness", SCRIPT)
assert MODULE_SPEC and MODULE_SPEC.loader
READINESS = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(READINESS)


class ReadinessEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Readiness Test")
        (self.repo / ".gitignore").write_text("logs/\ntemp/\n", encoding="utf-8")
        (self.repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        role = self.repo / ".agents/roles/CODE_PROJECT_MANAGER.md"
        role.parent.mkdir(parents=True)
        role.write_text("session_owner_id=test-session\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")
        self.candidate = self._git("rev-parse", "HEAD")
        self.exercise = "logs/readiness"
        self.ticketing = READINESS.ticketing
        self.ticketing.REGISTERED_REPOSITORY = self.repo
        self.ticketing.WORKTREE_ROOT = self.repo / "temp/worktrees/HMASD"
        treatment_handoff = (
            Path(self.ticketing.TREATMENT_TRANSPORT_DIRECTORY) / "TREATMENT.json"
        ).as_posix()
        self.ticketing.provision_ticket(
            argparse.Namespace(
                repo=self.repo,
                assignment_id="TREATMENT",
                base_commit=self.candidate,
                allow=["candidate.txt", treatment_handoff],
            )
        )
        bindings = self.repo / "temp/sessions/research_scheduler/bindings"
        bindings.mkdir(parents=True)
        (bindings / "TREATMENT.json").write_text(
            json.dumps(
                {
                    "assignment_id": "TREATMENT",
                    "session_id": "test-session",
                    "owner_role": "code_project_manager",
                    "owner_mode": "treatment",
                    "allowed_write_paths": ["candidate.txt", treatment_handoff],
                    "active": True,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()

    def _spec(self, *, fail_phase: str | None = None, attempt: str = "a1") -> Path:
        phases = {}
        for name in READINESS.PHASES:
            code = "print('阶段-✓')"
            if name == READINESS.PHASES[0]:
                code += "; open('logs/readiness/artifact.txt', 'w', encoding='utf-8').write('ok')"
            if name == fail_phase:
                code += "; raise SystemExit(7)"
            phases[name] = {
                "argv": [sys.executable, "-X", "utf8", "-c", code],
                "timeout_seconds": 5,
            }
        value = {
            "schema_version": 3,
            "candidate_commit": self.candidate,
            "attempt_id": attempt,
            "trigger": "focused test",
            "exact_paths": ["candidate.txt"],
            "formal": False,
            "scientific_iteration_cost": 0,
            "exercise_root": self.exercise,
            "expected_artifacts": ["logs/readiness/artifact.txt"],
            "phases": phases,
        }
        path = Path(self.tmp.name) / f"spec-{attempt}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def _hook_output(
        self,
        receipt: Path,
        *,
        session_id: object = "test-session",
        include_session_id: bool = True,
        cwd: object | None = None,
        include_cwd: bool = True,
    ) -> str:
        payload = {
            "last_assistant_message": "\n".join(
                (
                    "CODE_ACCEPTED",
                    f"commit={self._git('rev-parse', 'HEAD')}",
                    "exact_paths=candidate.txt",
                    "execution_readiness=passed",
                    f"execution_readiness_receipt={receipt}",
                )
            ),
        }
        if include_cwd:
            payload["cwd"] = str(self.repo) if cwd is None else cwd
        if include_session_id:
            payload["session_id"] = session_id
        old_stdin, old_stdout = sys.stdin, sys.stdout
        output = io.StringIO()
        try:
            sys.stdin = io.StringIO(json.dumps(payload))
            sys.stdout = output
            self.assertEqual(READINESS.hook_stop(), 0)
        finally:
            sys.stdin, sys.stdout = old_stdin, old_stdout
        return output.getvalue()

    def test_hook_requires_exact_treatment_session_identity(self) -> None:
        spec = self._spec()
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            self.assertEqual(READINESS.run_spec(spec), 0)
            self.assertEqual(READINESS.finalize_spec(spec), 0)
            final = self.repo / ".git/hmasd/execution-readiness" / self.candidate / "a1.json"

            self.assertEqual(self._hook_output(final), "")
            invalid = (
                self._hook_output(final, include_session_id=False),
                self._hook_output(final, session_id=None),
                self._hook_output(final, session_id=123),
                self._hook_output(final, session_id=""),
                self._hook_output(final, session_id="wrong-session"),
            )
            for output in invalid:
                payload = json.loads(output)
                self.assertEqual(payload["decision"], "block")
                self.assertIn("session_id", payload["reason"])
        finally:
            os.chdir(old)

    def test_hook_workspace_resolution_fail_closed_after_code_accepted(self) -> None:
        receipt = self.repo / "not-used.json"
        missing_cwd = json.loads(self._hook_output(receipt, include_cwd=False))
        self.assertEqual(missing_cwd["decision"], "block")
        self.assertIn("cwd", missing_cwd["reason"])

        invalid_cwd = json.loads(
            self._hook_output(receipt, cwd=str(self.repo / "missing-repository"))
        )
        self.assertEqual(invalid_cwd["decision"], "block")
        self.assertTrue(invalid_cwd["reason"])

    def test_hook_exact_integration_session_is_a_treatment_noop(self) -> None:
        spec = self._spec()
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            self.assertEqual(READINESS.run_spec(spec), 0)
            self.assertEqual(READINESS.finalize_spec(spec), 0)
            final = self.repo / ".git/hmasd/execution-readiness" / self.candidate / "a1.json"
            bindings = self.repo / "temp/sessions/research_scheduler/bindings"
            (bindings / "INTEGRATION.json").write_text(
                json.dumps(
                    {
                        "assignment_id": "INTEGRATION",
                        "session_id": "integration-session",
                        "owner_role": "code_project_manager",
                        "owner_mode": "integration",
                        "allowed_write_paths": ["candidate.txt"],
                        "active": True,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(self._hook_output(final, session_id="integration-session"), "")
        finally:
            os.chdir(old)

    def test_ordered_run_logs_utf8_and_finalize_is_idempotent(self) -> None:
        spec = self._spec()
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            self.assertEqual(READINESS.run_spec(spec), 0)
            self.assertEqual(READINESS.finalize_spec(spec), 0)
            final = self.repo / ".git/hmasd/execution-readiness" / self.candidate / "a1.json"
            before = final.read_bytes()
            self.assertEqual(READINESS.finalize_spec(spec), 0)
            self.assertEqual(final.read_bytes(), before)
            self.assertEqual(READINESS.check_receipt(final), 0)
            self.assertEqual(self._hook_output(final), "")
            receipt = json.loads(before)
            self.assertEqual(receipt["candidate_commit"], self.candidate)
            self.assertEqual([p["name"] for p in receipt["phases"]], list(READINESS.PHASES))
            self.assertIn("阶段-✓", receipt["phases"][0]["stdout_tail"])
            self.assertTrue((self.repo / "logs/readiness/.hmasd-readiness-logs/interface_smoke.stdout").is_file())
            (self.repo / "successor.txt").write_text("next\n", encoding="utf-8")
            self._git("add", "successor.txt")
            self._git("commit", "-qm", "advance head")
            self.assertEqual(READINESS.check_receipt(final), 0)
        finally:
            os.chdir(old)

    def test_first_failure_stops_and_typed_timeout_is_recorded(self) -> None:
        spec = self._spec(fail_phase="bounded_exercise")
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            self.assertEqual(READINESS.run_spec(spec), 1)
            self.assertFalse((self.repo / "logs/readiness/.hmasd-readiness-candidate.json").exists())
            result = READINESS._run_phase(
                self.repo,
                self.repo / "logs/readiness",
                "timeout",
                {"argv": [sys.executable, "-X", "utf8", "-c", "import time; time.sleep(3)"], "timeout_seconds": 1},
            )
            self.assertEqual(result["status"], "FAILED")
            self.assertIn(result["failure_kind"], {"timeout", "process_tree_termination_failed"})
            self.assertIn("process_tree_terminated", result)
        finally:
            os.chdir(old)

    def test_dirty_candidate_is_rejected(self) -> None:
        (self.repo / "candidate.txt").write_text("dirty\n", encoding="utf-8")
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            with self.assertRaises(READINESS.ReadinessError):
                READINESS._load_spec(self._spec(), self.repo, fresh=True, require_current_head=True)
        finally:
            os.chdir(old)

    def test_existing_empty_exercise_root_is_rejected(self) -> None:
        (self.repo / self.exercise).mkdir(parents=True)
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            with self.assertRaisesRegex(READINESS.ReadinessError, "must be absent"):
                READINESS._load_spec(self._spec(), self.repo, fresh=True, require_current_head=True)
        finally:
            os.chdir(old)

    def test_launch_error_and_phase_git_mutation_are_typed(self) -> None:
        spec = self._spec()
        value = json.loads(spec.read_text(encoding="utf-8"))
        value["phases"]["interface_smoke"]["argv"] = [
            sys.executable,
            "-X",
            "utf8",
            "-c",
            "open('candidate.txt', 'w', encoding='utf-8').write('changed'); "
            "open('logs/readiness/artifact.txt', 'w', encoding='utf-8').write('ok')",
        ]
        spec.write_text(json.dumps(value), encoding="utf-8")
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            launch = READINESS._run_phase(
                self.repo,
                self.repo / "logs/launch",
                "launch",
                {"argv": [str(self.repo / "definitely-missing-command")], "timeout_seconds": 1},
            )
            self.assertEqual(launch["failure_kind"], "launch_error")
            collision_root = self.repo / "logs/launch-collision"
            (collision_root / ".hmasd-readiness-logs/launch.stdout").mkdir(parents=True)
            log_failure = READINESS._run_phase(
                self.repo,
                collision_root,
                "launch",
                {"argv": [str(self.repo / "definitely-missing-command")], "timeout_seconds": 1},
            )
            self.assertEqual(log_failure["failure_kind"], "log_write_error")
            self.assertEqual(READINESS.run_spec(spec), 1)
            self.assertFalse((self.repo / "logs/readiness/.hmasd-readiness-candidate.json").exists())
        finally:
            os.chdir(old)

    def test_tampered_candidate_and_conflicting_final_receipts_fail_closed(self) -> None:
        spec = self._spec()
        old = Path.cwd()
        os.chdir(self.repo)
        try:
            self.assertEqual(READINESS.run_spec(spec), 0)
            candidate_path = self.repo / "logs/readiness/.hmasd-readiness-candidate.json"
            self.assertIn('"decision": "block"', self._hook_output(candidate_path))
            final = self.repo / ".git/hmasd/execution-readiness" / self.candidate / "a1.json"
            final.parent.mkdir(parents=True)
            final.write_text(json.dumps({"different": True}), encoding="utf-8")
            with self.assertRaises(READINESS.ReadinessError):
                READINESS.finalize_spec(spec)
            candidate_path.write_text(json.dumps({"status": "PASSED"}), encoding="utf-8")
            with self.assertRaises(READINESS.ReadinessError):
                READINESS.finalize_spec(spec)
        finally:
            os.chdir(old)


if __name__ == "__main__":
    unittest.main()
