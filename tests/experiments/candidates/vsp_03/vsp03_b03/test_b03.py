"""No model construction, RNG draw, rollout, or optimizer call in these checks."""
import ast
import math
from pathlib import Path

from experiments.candidates.vsp_03.vsp03_b02.b02 import difference
from experiments.candidates.vsp_03.vsp03_b01.b01 import write_json

ROOT = Path(__file__).resolve().parents[5]


def test_single_g_connections_and_endpoint():
    source = (ROOT / "experiments/candidates/vsp_03/vsp03_b03/b03.py").read_text()
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert len([n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "Model"]) == 1
    assert 'arm_index, arm = 1, "G"' in source
    assert 'action_tapes(seed, 100, 0, arm_index, first, 128)' in source
    assert 'action_tapes(seed, 200, 1, arm_index, 0, 1024)' in source
    assert 'range(1, 129)' in source
    assert 'worlds(seed, 200, 0, 1024)' in source
    assert 'for mode in ("greedy", "stochastic")' in source
    assert 'for rule in ("R", "R0")' in source
    assert 'summary["primary"] = summary["comparisons"]["G_greedy-R0"]' in source
    assert '"independent_training_instances": 1' in source
    assert 'focused_check' not in source and 'independent_training_pairs' not in source
    assert '"T"' not in source
    imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(a.name == "run" for n in imports for a in n.names)
    assert 'persisted["arms"] == summary["arms"]' in source
    assert 'torch.load(out / f"{arm}_final.pt"' in source
    assert 128 * 128 + 4 * 1024 == 20480
    assert (128 * 128 + 4 * 1024) * 40 * 2 == 1638400


def test_literal_primary_and_publication(tmp_path):
    # Literal endpoint values, not new scientific observations.
    result = difference([{"return": 0.1}, {"return": -0.2}],
                        [{"return": 0.0}, {"return": 0.0}])
    assert math.isclose(result["mean"], -0.05)
    assert math.isclose(result["conditional_world_sd"], 0.3 / math.sqrt(2))
    assert math.isclose(result["conditional_world_se"], 0.15)
    assert write_json(tmp_path / "literal.json", {"primary": result}) == {"primary": result}


def test_runner_seed_thread_and_clock_connection():
    source = (ROOT / "scripts/run_vsp03_b03.py").read_text()
    compile(source, "run_vsp03_b03.py", "exec")
    assert 'choices=[5], default=5' in source
    assert source.index('os.environ[variable] = "1"') < source.index('from experiments.')
    assert 'args.started_monotonic' in source
    assert 'os.environ["VSP03_B03_COMMAND"]' in source
