"""Read the P59 traceback's source locations without importing the workload.

Run directly with ``python -I -B <this file>`` against the P59 source recorded
in the technical result. This parses source text only; it neither executes
the parsed code nor diagnoses a native memory fault.
"""

import ast
import json
from pathlib import Path
import sys
import time


def main():
    started = time.perf_counter()
    root = Path(__file__).resolve().parents[4]
    direction = "experiments/candidates/finite_resource_relational_inductive_efficiency/"
    traceback = (
        (direction + "rng.py", 133),
        (direction + "rng.py", 204),
        (direction + "rng.py", 251),
        (direction + "rng.py", 273),
        (direction + "tapes.py", 373),
        (direction + "b01_contact_r02/tapes.py", 247),
        (direction + "b01_contact_r02/tapes.py", 246),
        ("tests/" + direction + "native_crash_repair/test_training_input_factory.py", 22),
        ("tests/" + direction + "native_crash_repair/test_training_input_factory.py", 39),
    )
    extra_sources = (
        direction + "b01_contact_r02/experiment.py",
        direction + "contracts/core.py",
    )
    paths = tuple(dict.fromkeys(path for path, _ in traceback)) + extra_sources
    sources = {}
    for path in paths:
        text = (root / path).read_text(encoding="utf-8")
        sources[path] = (text.splitlines(), ast.parse(text, filename=path))
    frames = []
    for path, line in traceback:
        lines, tree = sources[path]
        functions = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.lineno <= line <= node.end_lineno
        ]
        function = min(functions, key=lambda node: node.end_lineno - node.lineno, default=None)
        frames.append({
            "path": path, "reported_line": line,
            "source_line": lines[line - 1].strip(),
            "containing_function": function.name if function else "<module>",
            "definition_line": function.lineno if function else None,
            "first_body_line": function.body[0].lineno if function else None,
            "is_definition_line": function is not None and line == function.lineno,
            "calls_covering_reported_line": sorted({
                ast.unparse(node.func) for node in ast.walk(tree)
                if isinstance(node, ast.Call) and node.lineno <= line <= node.end_lineno
            }),
        })
    print(json.dumps({
        "mode": "source_ast_only",
        "python": sys.version,
        "files_parsed": len(sources),
        "lines_parsed": sum(len(lines) for lines, _ in sources.values()),
        "frames": frames,
        "workload_modules_loaded": sorted(
            name for name in sys.modules
            if name == "experiments" or name.startswith("experiments.")
            or name in ("numpy", "torch")
        ),
        "wall_seconds": time.perf_counter() - started,
    }, indent=2))


if __name__ == "__main__":
    main()
