"""Static/symbolic B06 law checks; no Torch import, numerical fixture or files."""
import ast
import contextlib
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[5]
DIRECTION = ROOT / "experiments/candidates/roster_consistent_latent_exploration"


def tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def definition(module, name):
    return next(node for node in module.body if getattr(node, "name", None) == name)


def constant(module, name):
    return ast.literal_eval(next(node.value for node in module.body
                                if isinstance(node, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)))


class Zero:
    def zero_(self):
        return self


class Symbol:
    def __init__(self, events):
        self.events = events

    def __getitem__(self, index):
        self.events.append(("field", index))
        return self

    def abs(self):
        self.events.append(("abs",))
        return self

    def argmin(self, **kwargs):
        self.events.append(("argmin", kwargs))
        return self

    def scatter_(self, dimension, nearest, offset):
        self.events.append(("scatter", dimension, nearest, offset))
        return self

    def __add__(self, other):
        return ("added", self, other)


class Base:
    def __init__(self):
        self.pointer_score = SimpleNamespace(weight=Zero(), bias=Zero())

    def pointer_logits(self, pointer):
        return pointer

    def state_dict(self):
        return {"symbolic": "retained-state"}

    def load_state_dict(self, state):
        self.loaded = state


class LawBinding(unittest.TestCase):
    def test_model_offset_and_saved_law(self):
        shared = tree(DIRECTION / "b04_nearest_prior/study.py")
        fresh = tree(DIRECTION / "b06_nearest99_prior1000/study.py")
        old, new = constant(shared, "LAW"), constant(fresh, "LAW")
        self.assertEqual((old["nearest_probability"], old["other_probability"]), (.9, .02))
        self.assertEqual((new["nearest_probability"], new["other_probability"]), (.99, .002))
        self.assertEqual(new["nearest_probability"] + 5 * new["other_probability"], 1)
        events, saved = [], []
        returned_probability = object()
        def softmax(value, **kwargs):
            events.append(("softmax", value, kwargs))
            return returned_probability
        namespace = dict(LAW=old, TBCFVModel=Base, math=math,
                         torch=SimpleNamespace(zeros_like=lambda x: Symbol(events),
                                               softmax=softmax, no_grad=contextlib.nullcontext,
                                               save=lambda value, path: saved.append((value, path))),
                         b03=SimpleNamespace(FLEX="FLEX",
                                             initialize_block_models=lambda rng: {"FLEX": Base()}))
        nodes = [definition(shared, name) for name in ("NearestPriorModel", "initialize_model", "save_model")]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<symbolic-law>", "exec"), namespace)
        for law, odds in ((None, 45), (new, 495)):
            events.clear()
            model = namespace["initialize_model"]("supplied-symbol", action_law=law)
            self.assertIsNot(model.action_law, old if law is None else new)
            pointer = Symbol(events)
            self.assertIs(model.claim_probabilities(pointer), returned_probability)
            self.assertIn(("field", (Ellipsis, 76)), events)
            self.assertIn(("abs",), events)
            self.assertIn(("argmin", {"dim": -1, "keepdim": True}), events)
            self.assertIn(("scatter", -1, pointer, math.log(odds)), events)
            self.assertEqual(events[-1][0], "softmax")
            self.assertEqual(events[-1][1][0], "added")
            self.assertEqual(events[-1][2], {"dim": -1})
            namespace["save_model"](model, "symbolic-path")
            payload, path = saved[-1]
            self.assertEqual(path, "symbolic-path")
            self.assertEqual(set(payload), {"state_dict", "action_law", "model"})
            self.assertEqual(payload["action_law"], old if law is None else new)
            self.assertEqual(payload["model"], "NearestPriorModel")
            restored = namespace["NearestPriorModel"](action_law=payload["action_law"])
            restored.load_state_dict(payload["state_dict"])
            self.assertEqual(restored.action_law, model.action_law)
            self.assertEqual(restored.loaded, model.state_dict())

    def test_entry_initialization_and_summary_bindings(self):
        captured = []
        fake_shared = SimpleNamespace(host="symbolic-host",
                                      run=lambda *args, **kw: captured.append((args, kw)))
        for attempt, seed, panel in (("b05_nearest_prior1000", 25, "B05"),
                                     ("b06_nearest99_prior1000", 26, "B06")):
            module = tree(DIRECTION / attempt / "study.py")
            namespace = {"b04": fake_shared}
            nodes = [n for n in module.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
            exec(compile(ast.Module(body=nodes, type_ignores=[]), "<entry-stub>", "exec"), namespace)
            namespace["run"]("learned", "out", "sha", "admission", "start", "cap")
            args, keywords = captured[-1]
            self.assertEqual(args[-1], seed)
            self.assertEqual(keywords["updates"], 1000)
            self.assertEqual(keywords["panel_label"], panel)
            self.assertEqual(keywords["object_id"], namespace["OBJECT_ID"])
            if panel == "B06":
                self.assertIs(keywords["action_law"], namespace["LAW"])
            else:
                self.assertNotIn("action_law", keywords)
        shared = tree(DIRECTION / "b04_nearest_prior/study.py")
        run = definition(shared, "run")
        defaults = dict(zip((a.arg for a in run.args.kwonlyargs), run.args.kw_defaults))
        self.assertIsNone(ast.literal_eval(defaults["action_law"]))
        calls = [n for n in ast.walk(run) if isinstance(n, ast.Call)]
        init = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "initialize_model")
        self.assertEqual(ast.unparse(next(k.value for k in init.keywords if k.arg == "action_law")), "action_law")
        summary = next(n.value for n in run.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "summary" for t in n.targets))
        self.assertEqual(ast.unparse(next(k.value for k in summary.keywords if k.arg == "action_law")), "action_law")
        reference_if = next(n for n in ast.walk(run) if isinstance(n, ast.If) and ast.unparse(n.test) == "arm == 'learned'")
        self.assertTrue(any(isinstance(n, ast.Call) and ast.unparse(n.func) == "comparisons"
                            for statement in reference_if.orelse for n in ast.walk(statement)))
        entry = (ROOT / "scripts/run_rcle_b06_nearest99_prior1000.py").read_text()
        self.assertIn('choices=(26,), default=26', entry)
        self.assertIn("b06_nearest99_prior1000.study import run, host", entry)
        ast.parse(entry)
        wrapper = (ROOT / "scripts/run_rcle_b06_nearest99_prior1000.sh").read_text()
        self.assertEqual(wrapper.count("--seed 26"), 2)
        self.assertEqual(wrapper.count("admit-memory"), 2)
        self.assertIn("timeout 600", wrapper)
        self.assertIn("timeout 10", wrapper)
        self.assertEqual(wrapper.count(" && "), 2)

    def test_six_unchanged_reading_rows(self):
        direction = ROOT / "docs/research/candidates/roster_consistent_latent_exploration"
        def rows(name):
            return [line for line in (direction / name).read_text(encoding="utf-8").splitlines()
                    if line.startswith("| ") and not line.startswith(("| Observation", "| ---"))]
        old = rows("RCLE_B05_NEAREST_PRIOR1000_SCIENCE_CARD_20260911.md")
        new = rows("RCLE_B06_NEAREST99_PRIOR1000_SCIENCE_CARD_20260911.md")
        self.assertEqual(len(old), 6)
        self.assertEqual(new, old)


if __name__ == "__main__":
    unittest.main(verbosity=2)
