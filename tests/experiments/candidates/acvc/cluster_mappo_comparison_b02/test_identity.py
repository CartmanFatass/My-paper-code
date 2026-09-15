"""Block-2 identity binding: fresh master/namespace, every recipe constant unchanged, no early import."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


@pytest.fixture
def fresh_modules():
    names = [n for n in list(sys.modules) if "cluster_mappo_comparison_b0" in n]
    saved = {n: sys.modules.pop(n) for n in names}
    yield
    for n in [n for n in list(sys.modules) if "cluster_mappo_comparison_b0" in n]:
        sys.modules.pop(n)
    sys.modules.update(saved)


def test_bind_block_rebinds_identities_and_keeps_the_recipe(fresh_modules):
    b02 = importlib.import_module("run_acvc_cluster_mappo_comparison_b02")
    p = b02.p
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28331, 38331)
    frozen = {name: getattr(p, name) for name in b02.FROZEN}
    b02.bind_block()
    assert (p.MASTER, p.EVALUATION_NAMESPACE) == (28431, 38431)
    assert p.OBJECT == "ACVC_CLUSTER_MAPPO_COMPARISON_B02"
    for name, value in frozen.items():
        assert getattr(p, name) is value
    assert frozen["TRAIN_EPISODES"] == 4096 and frozen["EVAL_EPISODES"] == 64 and frozen["HORIZON"] == 256
    assert frozen["UPSTREAM_SHA"] == "de66d7a4b23fac2513f56f96f73b3f5cb96695ac"
    # Derived seeds of the new block never collide with block 1's: the largest offset in the recipe's
    # seed graph is base + 40463 (native_link_loss_b01/model.py eval gate generators), far below the
    # 100000 * 100 gap between the two masters and the two namespaces.
    span = range(0, 50000)
    old = {100000 * 28331 + k for k in span} | {100000 * 38331 + k for k in span}
    new = {100000 * 28431 + k for k in span} | {100000 * 38431 + k for k in span}
    assert not (old & new)
    # The B01 runner's parser now accepts only the block-2 seed.
    parser_choices = None
    import argparse
    original = argparse.ArgumentParser.add_argument
    def spy(self, *args, **kwargs):
        nonlocal parser_choices
        if args and args[0] == "--seed":
            parser_choices = kwargs.get("choices")
        return original(self, *args, **kwargs)
    argparse.ArgumentParser.add_argument = spy
    try:
        with pytest.raises(SystemExit):
            b02.b01.main(["--mode", "run", "--output", "x"])  # parser error: no arm/launch sha
    finally:
        argparse.ArgumentParser.add_argument = original
    assert parser_choices == [28431]


def test_early_recipe_import_is_refused(fresh_modules):
    b02 = importlib.import_module("run_acvc_cluster_mappo_comparison_b02")
    sys.modules["experiments.candidates.acvc.cluster_mappo_comparison_b01.c_fit"] = object()
    with pytest.raises(RuntimeError):
        b02.bind_block()


def test_wrong_seed_is_refused(fresh_modules):
    b02 = importlib.import_module("run_acvc_cluster_mappo_comparison_b02")
    with pytest.raises(SystemExit):
        b02.main(["--seed", "28331", "--output", "x", "--arm", "C", "--launch-sha", "abc"])
    with pytest.raises(SystemExit):
        b02.main(["--output", "x", "--arm", "C", "--launch-sha", "abc", "--seed"])
