"""Static B04 binding checks; no imports of scientific modules or generated scratch."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def test_new_seed_object_and_preserved_b03_binding():
    old = (ROOT / "scripts/run_vsp03_b03.py").read_text()
    new = (ROOT / "scripts/run_vsp03_b04.py").read_text()
    assert 'choices=[5], default=5' in old
    assert 'os.environ["VSP03_B03_COMMAND"]' in old
    assert 'choices=[6], default=6' in new
    tree = ast.parse(new)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == "run")
    assert ast.unparse(call.args[0]) == "args.seed"
    assert ast.literal_eval(next(k.value for k in call.keywords if k.arg == "object_name")) == "VSP03_B04"
    assert 'vsp03_b03.b03 import run' in new
    assert 'os.environ["VSP03_B04_COMMAND"]' in new
    assert new.index('os.environ[variable] = "1"') < new.index('from experiments.')


def test_shared_driver_default_and_arm_stay_bound():
    source = (ROOT / "experiments/candidates/vsp_03/vsp03_b03/b03.py").read_text()
    tree = ast.parse(source)
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    assert run.args.args[-1].arg == "object_name"
    assert ast.literal_eval(run.args.defaults[-1]) == "VSP03_B03"
    assert 'summary = {"object": object_name,' in source
    assert 'arm_index, arm = 1, "G"' in source
    assert '"initialization": 40000 + seed' in source
    assert '"independent_training_instances": 1' in source
