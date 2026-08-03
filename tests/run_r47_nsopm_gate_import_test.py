from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R47_RUNNER = ROOT / "scripts" / "run_r47_nsopm_gate.py"
SMOKE = ROOT / "ha_ctse_process" / "smoke.py"


def _imports(path: Path) -> set[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        (str(node.module), alias.name)
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def test_r47_and_smoke_use_direct_module_owners() -> None:
    runner_source = R47_RUNNER.read_text(encoding="utf-8")
    runner_tree = ast.parse(runner_source)
    imports = _imports(R47_RUNNER)

    assert ("ha_ctse_process.standalone_cli", "create_env") in imports
    assert ("ha_ctse_process.standalone_cli", "create_agent") in imports
    assert "train_mod" not in runner_source
    assert {
        node.func.id
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } >= {"create_env", "create_agent"}

    smoke_source = SMOKE.read_text(encoding="utf-8")
    assert "process_train" not in smoke_source
    assert not any(module == "ha_ctse_process" and name == "train" for module, name in _imports(SMOKE))
