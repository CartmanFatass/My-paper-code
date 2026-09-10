"""Focused protocol checks. Run from the maintained HMASD checkout with python -B."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch_parent = SOURCE.parent / "temp/tests"
        scratch_parent.mkdir(parents=True, exist_ok=True)
        cls.scratch = Path(tempfile.mkdtemp(prefix="codex-benchmark-", dir=scratch_parent)).resolve()
        cls.parent = scratch_parent.resolve()

    @classmethod
    def tearDownClass(cls):
        if cls.scratch.parent != cls.parent or not cls.scratch.name.startswith("codex-benchmark-"):
            raise RuntimeError("Unexpected cleanup path")
        shutil.rmtree(cls.scratch)
        if cls.scratch.exists():
            raise RuntimeError("Scratch cleanup incomplete")

    def setUp(self):
        self.base = self.scratch / self._testMethodName
        (self.base / "_host/root_delegation").mkdir(parents=True)
        (self.base / "root_delegation").mkdir()
        shutil.copy2(SOURCE / "runner.py", self.base / "runner.py")
        for name in ("EVENTS.md", "GRADING.md"):
            shutil.copy2(SOURCE / "_host/root_delegation" / name, self.base / "_host/root_delegation" / name)
        shutil.copy2(SOURCE / "root_delegation/ROOT_PROMPT.md", self.base / "root_delegation/ROOT_PROMPT.md")
        output = self.call("start", "--label", "PROTOCOL_TEST_NOT_MODEL_RESULT")
        self.run_id = output.split("RUN_ID=", 1)[1].splitlines()[0]

    def call(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-B", str(self.base / "runner.py"), *args],
                                capture_output=True, encoding="utf-8", cwd=self.base)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def command(self, name, *args, ok=True):
        return self.call(name, "--run", self.run_id, *args, ok=ok)

    def answer(self, event, value="模拟测试答案，不是模型表现。"):
        path = self.base / "workspace/responses" / self.run_id / (event + ".md")
        path.write_text(value, encoding="utf-8")

    def test_complete_transcript_and_separate_grading(self):
        for number in range(1, 14):
            event = f"E{number:02}"
            output = self.command("next")
            self.assertTrue(output.startswith(event))
            if number in (7, 13):
                self.assertIn(event, self.command("evidence"))
            self.answer(event, f"独立协议测试答复 {event} 中文。")
            self.command("submit", "--event", event)
        self.assertIn("COMPLETE", self.command("next"))
        self.command("export")
        public = self.base / "workspace/responses" / self.run_id
        transcript = (public / "transcript.md").read_text(encoding="utf-8")
        for number in range(1, 14):
            self.assertIn(f"独立协议测试答复 E{number:02} 中文。", transcript)
        self.assertIn("No pending event", self.command("evidence", ok=False))
        self.assertNotIn("逐事件期望", transcript)
        summary = json.loads((public / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["events_submitted"], 13)
        self.assertEqual(summary["grade"], "not_run")
        self.assertEqual(summary["cost"], "unmeasured")
        review = self.base / "_host/runs" / self.run_id / "REVIEW_PROMPT.md"
        self.assertTrue(review.is_file())

    def test_pending_retry_invalid_and_duplicate_submission(self):
        self.command("evidence", ok=False)
        self.command("export", ok=False)
        first = self.command("next")
        self.assertEqual(first, self.command("next"))
        self.command("submit", "--event", "E02", ok=False)
        self.command("submit", "--event", "E01", ok=False)
        self.answer("E01", " \n")
        self.command("submit", "--event", "E01", ok=False)
        self.answer("E01")
        self.command("submit", "--event", "E01")
        self.command("submit", "--event", "E01", ok=False)
        status = json.loads(self.command("status"))
        self.assertEqual(status["submitted"], 1)
        self.assertIsNone(status["pending"])
        self.assertTrue(self.command("next").startswith("E02"))
        self.call("status", "--run", "../escape", ok=False)

    def test_frozen_inputs_and_current_evidence_only(self):
        (self.base / "_host/root_delegation/EVENTS.md").write_text("modified", encoding="utf-8")
        (self.base / "_host/root_delegation/GRADING.md").write_text("modified", encoding="utf-8")
        first = self.command("next")
        self.assertNotIn("E02", first)
        self.assertIn("未提供额外证据", self.command("evidence"))
        self.answer("E01")
        self.command("submit", "--event", "E01")
        self.command("next")
        self.assertIn("尚无resource receipt", self.command("evidence"))
        frozen = self.base / "_host/runs" / self.run_id / "GRADING.md"
        self.assertIn("逐事件期望", frozen.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
