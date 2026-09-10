"""Offline protocol checks. No model calls; reference runs are not benchmark samples."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import runner
from _host import completion, materials, runtime
from _host.task_bank import TASKS, apply_reference

SCIENTIFIC_PYTHON = None
SCRATCH_PARENT = None


def silent(call, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return call(*args)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="cm-runner-", dir=SCRATCH_PARENT)
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def options(self, **kwargs):
        result = dict(root=str(self.root), mode="delegation", seed=17, difficulty="mixed",
                      level="L2", delivery="reuse", python=SCIENTIFIC_PYTHON,
                      cm=["gpt-6-astra", "medium"], implementer=["gpt-5.6-terra", "high"],
                      reviewer=["gpt-6-astra", "high"], task_minutes=30)
        result.update(kwargs)
        return argparse.Namespace(**result)

    def test_sampling_and_level_isolation(self):
        seen = set()
        for seed in range(80):
            pair = runner.choose_tasks(seed)
            self.assertEqual(pair, runner.choose_tasks(seed))
            self.assertEqual([TASKS[p]["kind"] for p in pair], ["classic", "non_example"])
            self.assertNotEqual(TASKS[pair[0]]["difficulty"], TASKS[pair[1]]["difficulty"])
            seen.update(pair)
        self.assertEqual(seen, set(TASKS))
        for level in materials.LEVELS:
            for delivery in ("fresh", "reuse"):
                workspace = self.root / (level + delivery)
                state = vars(self.options(level=level, delivery=delivery)) | {"id": "fixture"}
                materials.install(workspace, state, BASE)
                files = runner.hashes(workspace)
                examples = [p for p in files if "examples/" in p]
                patterns = [p for p in files if "patterns/" in p and p.endswith(".md")]
                self.assertEqual(bool(examples), level == "L3" and delivery == "reuse")
                if delivery == "fresh":
                    self.assertFalse(patterns)
                if level == "L0" and delivery == "reuse":
                    self.assertEqual(patterns, ["materials/patterns/HANDOFF.md"])
                if delivery == "reuse" and level in ("L1", "L2"):
                    for file in patterns:
                        body = (workspace / file).read_text(encoding="utf-8")
                        self.assertNotIn("## L3", body)
                        if level == "L1":
                            self.assertNotIn("## L2", body)

    def test_complete_reference_episode_and_negative_evidence(self):
        # Work on a maintenance-copy, then mutate it after prepare: the run must keep
        # its own task2 bytes and oracle despite ordinary later bank maintenance.
        maintained = self.root / "maintained"
        shutil.copytree(BASE / "patterns", maintained / "patterns")
        shutil.copytree(BASE / "_host/task_bank", maintained / "_host/task_bank")
        for relative in ("runner.py", "_host/materials.py", "_host/events.py", "_host/runtime.py", "_host/completion.py", "_host/judge_schema.json", "_host/pricing.json"):
            shutil.copy2(BASE / relative, maintained / relative)
        with patch.object(runner, "BASE", maintained):
            directory = silent(runner.prepare, self.options())
        state = runner.read(directory / "state.json")
        workspace = Path(state["workspace"])
        later = state["tasks"][1]
        with (maintained / "_host/task_bank/catalog.py").open("a", encoding="utf-8") as source:
            source.write(f"\nSOURCES[{later!r}][{TASKS[later]['owned_paths'][0]!r}] = 'raise RuntimeError(\"changed bank\")'\n")
            for task in state["tasks"]:
                source.write(f"HIDDEN[{task!r}] = 'assert False, \"changed oracle\"'\n")
        self.assertFalse((workspace / ("cm_" + state["tasks"][1])).exists())
        # The candidate command never exposes host-only export/judge/prepare.
        denied = subprocess.run([sys.executable, "-B", "benchmark.py", "judge"], cwd=workspace,
                                capture_output=True, text=True)
        self.assertNotEqual(denied.returncode, 0)
        for position, task in enumerate(state["tasks"]):
            materials.write(workspace / f"work/{task}.md", "Reference protocol calibration; no candidate agents or model trial.\n")
            note = f"work/{task}.md"
            for boundary in runner.BOUNDARIES:
                state = runner.read(directory / "state.json")
                if boundary == "checked":
                    apply_reference(workspace, task)
                    outcome = subprocess.run([SCIENTIFIC_PYTHON, *TASKS[task]["public_command"]],
                        cwd=workspace, capture_output=True, text=True, timeout=30)
                    self.assertEqual(outcome.returncode, 0, outcome.stderr)
                    materials.write(workspace / f"work/handoffs/{task}.md", "Calibration fixture only.\n")
                    materials.write(workspace / f"work/reviews/{task}.md", "Calibration fixture; no actual reviewer.\n")
                if boundary == "accepted":
                    files = TASKS[task]["owned_paths"]
                    runner.git(workspace, "add", "--", *files)
                    runner.git(workspace, "commit", "-m", "Reference fixture repair", "--", *files)
                    runner.git(workspace, "push", "origin", "main")
                    if position == 1:
                        materials.write(workspace / "work/final.md", "Both reference repairs; this is not a model result.\n")
                        materials.write(workspace / "work/status.md", "Continuing the second task after the status question.\n")
                        runner.save(workspace / "work/background.json", {
                            "archive-A/seed19": {"status": "complete", "missing": []},
                            "archive-B/seed20": {"status": "incomplete", "missing": ["returns.json"]}})
                completed = subprocess.run([sys.executable, "-B", "benchmark.py", "checkpoint",
                    "--boundary", boundary, "--note", note], cwd=workspace,
                    capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(completed.returncode, 0, completed.stderr)
        state = runner.read(directory / "state.json")
        self.assertEqual(len(state["checkpoints"]), 8)
        self.assertTrue(state["finished"])
        judgement = runtime.judge(directory, state, BASE)
        self.assertTrue(judgement["behavior_passed"], judgement)
        self.assertTrue(judgement["protocol_artifacts_passed"], judgement)
        self.assertEqual(judgement["configuration"]["status"], "unmeasured")
        self.assertTrue(all(row["first_implementation"]["passed"] for row in judgement["tasks"]))
        # A pass-shaped report is diagnostic only unless the independent evaluator
        # actually exited successfully and supplied a distinct native session ID.
        state["launch"] = {"session_id": "candidate-root"}
        runner.save(directory / "export.json", {"configuration": {"status": "verified"}})
        runner.save(directory / "assessment/report.json", {"semantic_passed": True,
            "policy_adherence": "conforming", "native_workflow": "conforming"})
        fake = subprocess.CompletedProcess([], 0, json.dumps({"passed": True, "checks": []}), "")
        for exit_code, identity, wanted in ((1, "grader-root", None), (0, None, None),
                                           (0, "candidate-root", None), (0, "grader-root", True)):
            runner.save(directory / "assessment/completion.json", {"returncode": exit_code,
                "session_id": identity, "ended": "2026-09-10T03:00:10Z"})
            with patch.object(runtime.subprocess, "run", return_value=fake):
                checked = runtime.judge(directory, state, BASE)
            self.assertEqual(checked["full_run_passed"], wanted)
        materials.write(directory / "assessment/input.txt", "complete closed evidence")
        for semantic, wanted in ((False, False), (None, None), (True, None)):
            runner.save(directory / "assessment/report.json", {"semantic_passed": semantic,
                "policy_adherence": "insufficient_evidence", "native_workflow": "insufficient_evidence"})
            with patch.object(runtime.subprocess, "run", return_value=fake):
                checked = runtime.judge(directory, state, BASE)
            self.assertEqual(checked["full_run_passed"], wanted)
        with self.assertRaises(ValueError):
            runner.checkpoint(argparse.Namespace(boundary="accepted", note=note), directory, state)
        # Tamper only with calibration snapshot evidence, never a real submitted run.
        code = Path(state["checkpoints"][-1]["snapshot"]) / "code"
        runner.save(code / "work/background.json", {"archive-B/seed20": {"status": "complete"}})
        materials.write(code / "notes/neighbor.md", "Lost neighbor edit\n")
        first_accepted = next(c for c in state["checkpoints"] if c["boundary"] == "accepted")
        first_accepted["origin_head"] = state["base_commit"]
        # Reuse behavior outcomes: this check concerns evidence/receipt grading only.
        fake = subprocess.CompletedProcess([], 0, json.dumps({"passed": True, "checks": []}), "")
        with patch.object(runtime.subprocess, "run", return_value=fake):
            bad = runtime.judge(directory, state, BASE)
        failures = {x["name"] for x in bad["protocol_checks"] if not x["passed"]}
        self.assertIn("background_identity_and_completion", failures)
        self.assertIn("neighbor_edit_preserved", failures)
        self.assertIn("commits_pushed_to_local_origin:" + state["tasks"][0], failures)

    def test_runtime_metadata_is_not_self_report(self):
        state = vars(self.options())
        state["expected_models"] = {role: state[role] for role in ("cm", "implementer", "reviewer")}
        state["workspace"] = str(self.root)
        config = lambda model, effort: [{"model": model, "effort": effort}]
        rows = [{"id": "root", "agent_role": None, "turn_configurations": config(*state["cm"])},
                {"id": "review", "agent_role": "cm_reviewer", "turn_configurations": config(*state["reviewer"])},
                {"id": "worker", "agent_role": "cm_implementer", "turn_configurations": config(*state["implementer"])}]
        for row in rows:
            row["cwd"] = str(self.root)
        meta = {"root_session": "root", "sessions": rows}
        self.assertEqual(runtime.verify_configuration(state, meta)["status"], "verified")
        rows[2]["turn_configurations"] = config("gpt-6-astra", "medium")
        self.assertEqual(runtime.verify_configuration(state, meta)["status"], "mismatch")
        self.assertEqual(runtime.verify_configuration(state, {"sessions": []})["status"], "unmeasured")
        state["expected_models"] = {}
        rows[2]["agent_role"] = None
        self.assertEqual(runtime.verify_configuration(state, meta)["status"], "verified")
        self.assertIsNone(runtime.verify_configuration(state, meta)["observed_sessions"][2]["role"])
        rows[2]["turn_configurations"] = []
        self.assertEqual(runtime.verify_configuration(state, meta)["status"], "unmeasured")

    def test_inline_assessment_contains_closed_evidence(self):
        for name in ("candidate/tasks/task.md", "candidate/work/reviews/task.md", "first/task/code.py",
                     "POLICY.md", "behavior.json", "boundaries.json", "native_evidence.json"):
            materials.write(self.root / name, "中文 evidence " + name)
        materials.write(self.root / "candidate/temp/scratch.txt", "not evidence")
        packet = json.loads(runtime.assessment_packet(self.root))["closed_run_evidence_files"]
        self.assertEqual(len(packet), 7)
        self.assertTrue(all("中文" in item["content"] for item in packet))
        self.assertFalse(any("scratch" in item["path"] for item in packet))

    def test_cost_keeps_unicode_reports_with_legacy_stdout(self):
        runner.save(self.root / "export.json", {"runtime": {"root_session": "root"}})
        runner.save(self.root / "assessment/completion.json", {"session_id": "judge"})
        script = self.root / "cost.py"
        script.write_text("# fixture", encoding="utf-8")
        args = argparse.Namespace(script=script, pricing_json=None)
        out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
        completed = subprocess.CompletedProcess([], 0, "中文完整成本\n", "")
        with patch.object(runtime.subprocess, "run", return_value=completed), contextlib.redirect_stdout(out):
            runtime.cost(args, self.root, {}, BASE)
        self.assertEqual((self.root / "cost/team.md").read_text(encoding="utf-8"), "中文完整成本\n")
        self.assertEqual(set(runner.read(self.root / "cost/status.json")["results"]), {"team", "evaluator"})
        out.close()

    def test_native_export_keeps_edit_and_test_tools_not_reasoning(self):
        rollout = self.root / "rollout.jsonl"
        payloads = [
            {"type": "custom_tool_call", "name": "functions.exec", "call_id": "edit", "input": "public command"},
            {"type": "custom_tool_call_output", "call_id": "edit", "output": "test passed"},
            {"type": "function_call", "name": "spawn_agent", "call_id": "spawn", "arguments": "encrypted"},
            {"type": "function_call_output", "call_id": "spawn", "output": "child-id"},
            {"type": "message", "role": "assistant", "channel": "analysis", "content": "private"},
            {"type": "message", "role": "assistant", "channel": "final", "content": "public"},
            {"type": "reasoning", "content": "private"}]
        rollout.write_text("\n".join(json.dumps({"type": "response_item", "payload": p}) for p in payloads), encoding="utf-8")
        with sqlite3.connect(self.root / "state_5.sqlite") as db:
            db.execute("CREATE TABLE threads (id,source,cwd,model,reasoning_effort,agent_role,agent_path,cli_version,rollout_path,history_mode)")
            db.execute("INSERT INTO threads VALUES (?,?,?,?,?,?,?,?,?,?)",
                       ("root", '"cli"', str(self.root), "model", "high", None, None, "test", str(rollout), "full"))
        db.close()
        evidence = runtime.session_metadata(self.root, "root")["sessions"][0]["native_evidence"]
        self.assertEqual(len(evidence), 5)
        self.assertNotIn("private", json.dumps(evidence))
        self.assertIn("test passed", json.dumps(evidence))

    def test_report_distinguishes_unassessed_from_code_failure(self):
        state = {"id": "fixture", "seed": 17, "tasks": [], "task_metadata": {}}
        runner.save(self.root / "judgement.json", {"behavior_passed": True,
            "protocol_artifacts_passed": True, "full_run_passed": None,
            "semantic_review": {"semantic_passed": False, "policy_adherence": "insufficient_evidence"}})
        completion.report(self.root, state, "finished")
        report = (self.root / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("完整判定：未完成/无法确认", report)
        self.assertIn("独立代码语义：未完成/无法确认", report)
        materials.write(self.root / "assessment/input.txt", "complete closed evidence")
        completion.report(self.root, state, "finished")
        self.assertIn("独立代码语义：未通过", (self.root / "REPORT.md").read_text(encoding="utf-8"))

    def test_existing_session_begin_does_not_launch_a_cm(self):
        output = io.StringIO()
        with patch.object(runtime, "launch") as launch, contextlib.redirect_stdout(output):
            runner.main(["begin", "--mode", "direct", "--seed", "17", "--root", str(self.root),
                         "--session", "fixture-root", "--python", SCIENTIFIC_PYTHON])
        launch.assert_not_called()
        result = json.loads(output.getvalue())
        state = runner.read(Path(result["run"]) / "state.json")
        self.assertEqual(state["launch"]["session_id"], "fixture-root")
        self.assertEqual(state["launch"]["mode"], "existing_session")
        self.assertEqual(state["expected_models"], {})
        with patch.object(runtime, "session_metadata", return_value={"sessions": []}):
            exported = silent(runtime.export, argparse.Namespace(session="fixture-root", codex_home=str(self.root)),
                              Path(result["run"]), state, BASE)
        self.assertEqual(exported["requested"]["models"], {})
        self.assertEqual(exported["generated_role_defaults"]["cm"], ["gpt-6-astra", "medium"])
        entry = self.root / "cm_direct_review/workspace"
        self.assertTrue(Path(result["run"]).is_relative_to(entry))
        self.assertTrue(Path(result["workspace"]).is_relative_to(entry))
        self.assertNotIn("tasks", result)
        self.assertNotIn(state["tasks"][1], output.getvalue())

    def test_completion_uses_real_terminal_after_last_checkpoint(self):
        home = self.root / "codex-home"
        home.mkdir()
        rollout = home / "rollout.jsonl"
        with sqlite3.connect(home / "state_5.sqlite") as db:
            db.execute("CREATE TABLE threads (id TEXT, rollout_path TEXT, source TEXT)")
            db.execute("INSERT INTO threads VALUES (?,?,?)", ("fixture-root", str(rollout), '"cli"'))
        db.close()
        state = {"finished": "2026-09-10T03:00:00+00:00", "launch": {"codex_home": str(home), "session_id": "fixture-root"}}
        row = lambda stamp, kind: json.dumps({"timestamp": stamp, "type": "event_msg", "payload": {"type": kind}}) + "\n"
        rollout.write_text(row("2026-09-10T02:00:00Z", "task_complete"), encoding="utf-8")
        self.assertEqual(completion.closed_turn(state), "waiting")
        with rollout.open("a", encoding="utf-8") as out:
            out.write(row("2026-09-10T03:00:10Z", "task_complete"))
        self.assertEqual(completion.closed_turn(state), "complete")
        with sqlite3.connect(home / "state_5.sqlite") as db:
            db.execute("UPDATE threads SET source=?", (json.dumps({"subagent": {"thread_spawn": {"parent_thread_id": "other"}}}),))
        db.close()
        with self.assertRaises(ValueError):
            completion.closed_turn(state)

    def test_finalization_orders_collection_and_skips_grader_after_abort(self):
        for terminal in ("complete", "aborted"):
            directory = self.root / terminal
            state = {"id": terminal, "seed": 17, "tasks": ["fixture"],
                     "task_metadata": {"fixture": {"difficulty": "easy"}},
                     "runtime_dir": str(BASE), "launch": {"session_id": "root", "codex_home": str(self.root)}}
            runner.save(directory / "state.json", state)
            calls = []
            def tracked(name, result=None):
                def call(*args):
                    calls.append(name)
                    return result
                return call
            with patch.object(completion, "closed_turn", return_value=terminal), \
                    patch.object(runtime, "export", side_effect=tracked("export")), \
                    patch.object(runtime, "judge", side_effect=tracked("judge", {"full_run_passed": None})), \
                    patch.object(runtime, "assess", side_effect=tracked("assess")), \
                    patch.object(runtime, "cost", side_effect=tracked("cost")):
                completion.finalize(directory, state, BASE)
            expected = ["export", "judge", "assess", "cost"] if terminal == "complete" else ["export", "judge", "cost"]
            self.assertEqual(calls, expected)
            self.assertTrue((directory / "REPORT.md").is_file())
            self.assertEqual(runner.read(directory / "state.json")["finalizer"]["status"],
                             "finished" if terminal == "complete" else "cm_aborted_no_model_grader")

    def test_detached_finalizer_is_one_shot(self):
        directory = self.root / "run"
        directory.mkdir()
        state = {"runtime_dir": str(BASE)}
        with patch.object(completion.subprocess, "Popen") as popen:
            popen.return_value.pid = 123
            completion.detach(directory, state)
            completion.detach(directory, state)
        popen.assert_called_once()
        self.assertIn("finalize", popen.call_args.args[0])
        self.assertEqual(state["finalizer"]["status"], "waiting_for_cm_turn")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scientific-python", required=True)
    parser.add_argument("--scratch-parent", type=Path, required=True)
    args, remaining = parser.parse_known_args()
    SCIENTIFIC_PYTHON = args.scientific_python
    SCRATCH_PARENT = args.scratch_parent.resolve()
    if "temp" not in SCRATCH_PARENT.parts:
        raise ValueError("Use an invocation scratch parent under the checkout's temp/ directory")
    SCRATCH_PARENT.mkdir(parents=True, exist_ok=True)
    unittest.main(argv=[sys.argv[0], *remaining])
