"""Static/stub binding checks only: no scientific imports, tensors or episodes."""

import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[5]
NATIVE = ROOT / "experiments/candidates/metric_ground_transport_allocation/mgtap_top_query_b01/study.py"
ACCEPTED = ROOT / "experiments/candidates/metric_ground_transport_allocation/mgtap_top_query_b01/pair.py"
HELPERS = ROOT / "experiments/candidates/ucope/uav_motion_prefix_b01/study.py"


def stdlib_definitions(path, namespace, names=None):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
            if module and module.split(".")[0] in ("json", "math", "pathlib", "statistics", "subprocess", "time"):
                body.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if names is None or node.name in names:
                body.append(node)
        elif names is None and isinstance(node, ast.Assign):
            body.append(node)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), namespace)


class BindingTest(unittest.TestCase):
    def invoke(self, case, *, damage=False, fail=False, publication_fail=False):
        scratch = Path(os.environ["MGTAP_TEST_SCRATCH"]).resolve()
        self.assertTrue(scratch.is_relative_to((ROOT / "temp").resolve()))
        output = scratch / case
        self.assertFalse(output.exists())

        def cleanup_created_files():
            for name in ("summary.json", "episodes.jsonl", "rollouts.jsonl", "final_TOP.pt", "final_DENSE.pt"):
                (output / name).unlink(missing_ok=True)
            if output.exists():
                output.rmdir()  # unknown contents are preserved, never recursively removed
            if scratch.exists() and not any(scratch.iterdir()):
                scratch.rmdir()

        self.addCleanup(cleanup_created_files)
        ns = {"__file__": str(NATIVE), "TOP": "TOP", "DENSE": "DENSE"}
        stdlib_definitions(HELPERS, ns, {"Deadline", "clean_json", "new_counts", "write_summary"})
        stdlib_definitions(ACCEPTED, ns, {"reading", "primary", "publish_summary"})
        stdlib_definitions(NATIVE, ns)
        calls, events, train_streams, eval_streams = [], [], {}, {}

        def pair(seed):
            calls.append(seed)
            return {arm: (SimpleNamespace(arm=arm, state_dict=lambda: {}),
                          SimpleNamespace(arm=arm, state_dict=lambda: {}))
                    for arm in ("TOP", "DENSE")}

        def optimizer(actor, critic):
            self.assertEqual(actor.arm, critic.arm)
            events.append((actor.arm, "optimizer"))
            return actor.arm

        def collect(env, actor, critic, horizon, reset, velocity, duration,
                    metadata, check, counts, emit, diagnostic, limits, **options):
            arm, phase, e = metadata["arm"], metadata["phase"], metadata["episode"]
            self.assertEqual(options, dict(real=True, diagnostics=False, ratio_grouping="agent_compound"))
            self.assertEqual((env, horizon, actor.arm, critic.arm), (822101000, 256, arm, arm))
            self.assertEqual(reset, 822100000 + (1000 if phase == "train" else 2000) + e)
            self.assertEqual(duration.seed, metadata["duration_seed"])
            self.assertEqual(velocity.seed, metadata["velocity_seed"])
            if phase == "train":
                previous = train_streams.setdefault(arm, velocity)
                self.assertIs(previous, velocity)
            else:
                self.assertEqual(counts["optimizer_steps"], 1024)
                eval_streams[(arm, e)] = velocity
                self.assertTrue((output / f"final_{arm}.pt").is_file())
            check()
            if fail and (arm, phase, e) == ("DENSE", "train", 3):
                counts["team_steps"] += 3
                counts["train_team_steps"] += 3
                raise RuntimeError("supplied stub interruption")
            counts[f"{phase}_episodes"] += 1
            counts[f"{phase}_team_steps"] += horizon
            counts["team_steps"] += horizon
            counts["completed_episode_steps"] += horizon
            emit(dict(metadata, reset_seed=reset + int(damage and (arm, phase, e) == ("DENSE", "eval", 31)),
                      steps=horizon, J=1.02 if arm == "TOP" else 1.0))
            events.append((arm, phase, e))
            return (arm, phase, e)

        def update(actor, critic, opt, episodes, chunk, check, counts, **options):
            self.assertEqual(options, dict(ratio_grouping="agent_compound", entropy_coef=.01))
            self.assertEqual((opt, len(episodes), chunk), (actor.arm, 2, 32))
            self.assertTrue(all(e[0] == actor.arm and e[1] == "train" for e in episodes))
            counts["optimizer_steps"] += 4
            return [{"epoch": e} for e in range(4)]

        def save(value, path):
            Path(path).write_text(json.dumps(value), encoding="utf-8")

        ns.update(build_top_pair=pair, make_real=lambda seed: seed,
                  optimizer_for=optimizer, collect_episode=collect, update=update,
                  generator=lambda seed: SimpleNamespace(seed=seed), snapshot=lambda *args: {},
                  exposure=lambda *args: {"stub_only": True}, torch=SimpleNamespace(save=save))
        if publication_fail:
            def broken_publish(*args):
                raise OSError("supplied publication failure")
            ns["publish_summary"] = broken_publish
        result = ns["run_pair"](8221, output, 0.0, clock=lambda: .1)
        closed = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(closed["status"], result["status"])
        self.assertEqual(calls, [8221])
        self.assertEqual(result["top_level_model_constructions"], 6)
        self.assertIsNot(train_streams["TOP"], train_streams["DENSE"])
        self.assertEqual(train_streams["TOP"].seed, train_streams["DENSE"].seed)
        if not fail:
            self.assertEqual(len(eval_streams), 64)
            self.assertEqual(len({id(stream) for stream in eval_streams.values()}), 64)
            for e in range(32):
                self.assertEqual(eval_streams[("TOP", e)].seed, eval_streams[("DENSE", e)].seed)
        return result, output

    def test_exact_native_binding_and_closed_outputs(self):
        result, output = self.invoke("complete")
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["primary"]["complete"])
        self.assertEqual(result["binding_errors"], [])
        self.assertEqual(set(result["arms"]), {"TOP", "DENSE"})
        for key, expected in dict(train_episodes=1024, eval_episodes=64, team_steps=278528,
                                  optimizer_steps=2048, rollouts=512).items():
            self.assertEqual(result["counts"][key], expected)
        self.assertEqual(len((output / "episodes.jsonl").read_text().splitlines()), 1088)
        self.assertEqual(len((output / "rollouts.jsonl").read_text().splitlines()), 512)

    def test_world_binding_failure_withholds_paired_mean(self):
        result, _ = self.invoke("damaged_world", damage=True)
        self.assertFalse(result["primary"]["complete"])
        self.assertIsNone(result["primary"]["TOP_minus_DENSE"]["mean"])
        self.assertEqual(len(result["primary"]["J"]["DENSE"]), 32)

    def test_interrupted_fit_preserves_partial_counts_and_movement(self):
        result, _ = self.invoke("interrupted", fail=True)
        self.assertFalse(result["primary"]["complete"])
        self.assertTrue(result["arms"]["TOP"]["complete"])
        self.assertEqual(result["counts"]["partial_episode_steps"], 3)
        self.assertTrue(result["arms"]["DENSE"]["exposure"]["stub_only"])

    def test_publication_failure_retains_closed_fallback(self):
        result, _ = self.invoke("publication_failure", publication_fail=True)
        self.assertEqual(result["status"], "PUBLICATION_FAILED")
        self.assertTrue(any("supplied publication failure" in x for x in result["limits"]))


if __name__ == "__main__":
    unittest.main()
