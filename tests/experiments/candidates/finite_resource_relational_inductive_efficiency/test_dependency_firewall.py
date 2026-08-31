import ast
from pathlib import Path


def test_ast_dependency_firewall():
    package = Path(__file__).parents[4] / "experiments" / "candidates" / "finite_resource_relational_inductive_efficiency"
    forbidden = ("semantic_graphon_shared_policy", "vqfp_vnpa", "envs.native")
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(token in name.lower() for name in names for token in forbidden), path
