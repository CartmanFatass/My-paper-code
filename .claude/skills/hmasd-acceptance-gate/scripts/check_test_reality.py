"""Does the suite execute the code it claims to cover?

A green suite proves the assertions it ran. It says nothing about the production
paths it never entered. This checker asks three questions that string contracts
and pass-counts cannot:

  STUB_ONLY     a production symbol whose ONLY appearance in the tests is as a
                monkeypatch target. The suite replaces it everywhere and calls
                it nowhere, so its real body is never executed and any defect
                inside it is invisible.

  ENTRY_UNRUN   a production entry point (default `main`) that no test invokes.
                Every test builds its fixture by hand, so nothing asserts that
                the route the real run actually takes produces a conforming
                artifact.

  DEAD_PROD     a function defined in the source tree and referenced nowhere in
                it. A contract that says "fail closed unless X" while X is
                called by no production code has no executable closure.

Written 2026-07-28 after an adversarial review of the D7.S R4 instrument. The
suite was 249 green. `main()` was invoked by no test in either file;
`compute_u_star_bootstrap` appeared only as the `monkeypatch.setattr` that
replaces it; and `r4_freshness_sentinel` -- the function whose whole purpose is
refusing a non-conforming artifact -- was defined at line 1195 and called from
no production path at all. All three defects were invisible to the pass count.

This is a diagnostic, not a gate. It is invoked from `$hmasd-acceptance-gate`,
not from the pre-commit drift guard: it reasons about research code, which
changes constantly, and a blocking check there would stop unrelated work.

Exit 0 prints one OK line. Exit 1 prints one FINDING line per result.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def _public_defs(tree: ast.Module) -> dict[str, int]:
    """Top-level functions and classes, by name -> line."""
    out: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                out[node.name] = node.lineno
    return out


def _called_names(tree: ast.Module) -> set[str]:
    """Every name that appears in call position: f(...) and obj.f(...)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _referenced_names(tree: ast.Module) -> set[str]:
    """Every identifier read anywhere -- calls, aliases, decorators, exports.

    Deliberately wider than _called_names: a function passed as a callback or
    stored in a dispatch table is live even though it is never syntactically
    called. Only a name with no reference at all counts as dead.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # getattr(mod, "name") and __all__ entries keep a symbol live.
            names.add(node.value)
    return names


def _module_qualified_calls(tree: ast.Module) -> set[tuple[str, str]]:
    """(module, symbol) pairs a test actually invokes, resolved through imports.

    Entry points must be checked per module, not globally: `main` is defined by
    almost every script here, so a bare `main(` anywhere in the suite would mark
    all of them exercised. That false negative would hide exactly the defect this
    checker exists to find.
    """
    alias_to_module: dict[str, str] = {}
    direct: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                alias_to_module[a.asname or a.name.split(".")[0]] = a.name.split(".")[-1]
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.split(".")[-1]
            for a in node.names:
                direct.add((module, a.asname or a.name))

    # Modules named in string constants. This repository loads the module under
    # test with importlib.util.spec_from_file_location(...), so the binding is an
    # assignment, not an Import node, and alias resolution alone cannot see
    # `audit.main()`. Attributing attribute-calls to every module a file names in
    # a string over-approximates -- deliberately. A false ENTRY_UNRUN on a module
    # that IS exercised is the worse error: a checker that cries wolf gets
    # ignored, and then it protects nothing.
    loaded_by_path: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.replace("\\", "/")
            stem = text.rsplit("/", 1)[-1]
            if stem.endswith(".py"):
                loaded_by_path.add(stem[:-3])

    # Which local variables actually hold an importlib-loaded module. Without
    # this the crediting below is far too loose: every test file here ends with
    # `pytest.main([__file__, "-q"])`, so the attribute name `main` is present in
    # every file, and crediting it to any module named by a string constant
    # suppressed ENTRY_UNRUN on the very example this checker was written from.
    # Measured by the implementer: at the pre-repair baseline, blanking that one
    # footer line made the finding reappear.
    module_vars: set[str] = set()
    _LOADERS = {"module_from_spec", "import_module", "load_module", "SourceFileLoader"}

    def _callee(call: ast.Call) -> str | None:
        f = call.func
        if isinstance(f, ast.Attribute):
            return f.attr
        return f.id if isinstance(f, ast.Name) else None

    # One level of indirection: both test files here wrap the importlib dance in
    # a local `_load(name)` helper, so the module variable is assigned from that
    # helper, not from module_from_spec directly. Treating only the direct form
    # as a module variable made `pooling.main()` invisible.
    loader_funcs: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and _callee(inner) in _LOADERS:
                loader_funcs.add(node.name)
                break

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if _callee(node.value) not in (_LOADERS | loader_funcs):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                module_vars.add(target.id)

    calls: set[tuple[str, str]] = set()
    bare: set[str] = set()
    attribute_calls: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in module_vars:
                attribute_calls.add(func.attr)
            module = alias_to_module.get(func.value.id)
            if module:
                calls.add((module, func.attr))
        elif isinstance(func, ast.Name):
            bare.add(func.id)
    # A `from M import main` followed by a bare `main()` is a real invocation.
    for module, symbol in direct:
        if symbol in bare:
            calls.add((module, symbol))
    for module in loaded_by_path:
        for symbol in attribute_calls:
            calls.add((module, symbol))
    return calls


def _patch_targets(tree: ast.Module) -> set[str]:
    """Symbols replaced by monkeypatch.setattr / mock.patch.object.

    Handles the two forms that appear in this repository:
        monkeypatch.setattr(module, "symbol", replacement)
        monkeypatch.setattr("package.module.symbol", replacement)
    """
    targets: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr = func.attr if isinstance(func, ast.Attribute) else None
        if attr not in {"setattr", "object", "patch"}:
            continue
        for arg in node.args[:2]:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                targets.add(arg.value.rsplit(".", 1)[-1])
    return targets


def audit(source_dir: Path, tests_dir: Path, entry_points: set[str],
          ignore: set[str]) -> list[str]:
    findings: list[str] = []

    source_files = sorted(p for p in source_dir.rglob("*.py")
                          if "__pycache__" not in p.parts)
    test_files = sorted(p for p in tests_dir.rglob("*.py")
                        if "__pycache__" not in p.parts)
    if not source_files:
        return [f"no source modules under {source_dir}"]
    if not test_files:
        return [f"no test modules under {tests_dir}"]

    defs: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    source_refs: set[str] = set()
    for path in source_files:
        tree = _parse(path)
        if tree is None:
            findings.append(f"UNPARSEABLE {path}")
            continue
        for name, line in _public_defs(tree).items():
            defs[name].append((path, line))
        source_refs |= _referenced_names(tree)

    test_called: set[str] = set()
    test_patched: set[str] = set()
    test_qualified: set[tuple[str, str]] = set()
    for path in test_files:
        tree = _parse(path)
        if tree is None:
            findings.append(f"UNPARSEABLE {path}")
            continue
        test_called |= _called_names(tree)
        test_patched |= _patch_targets(tree)
        test_qualified |= _module_qualified_calls(tree)

    for name in sorted(test_patched):
        if name in ignore or name not in defs:
            continue
        if name in test_called:
            continue
        where = ", ".join(f"{p.as_posix()}:{ln}" for p, ln in defs[name])
        findings.append(
            f"STUB_ONLY {name} ({where}) -- replaced by a patch in the suite and "
            f"invoked by no test. Its real body never runs; a defect inside it "
            f"cannot turn the suite red.")

    for name in sorted(entry_points):
        if name in ignore or name not in defs:
            continue
        for path, line in defs[name]:
            if (path.stem, name) in test_qualified:
                continue
            findings.append(
                f"ENTRY_UNRUN {path.as_posix()}:{line} {path.stem}.{name} -- no test "
                f"invokes this module's production entry point. Every fixture is "
                f"hand-built, so nothing asserts that the route a real run takes "
                f"produces a conforming result.")

    for name, sites in sorted(defs.items()):
        if name in ignore or name in entry_points:
            continue
        # One reference is the definition's own binding; a live symbol has more.
        if name in source_refs:
            continue
        where = ", ".join(f"{p.as_posix()}:{ln}" for p, ln in sites)
        seen_in_tests = " (tests reference it, production does not)" if name in test_called else ""
        findings.append(
            f"DEAD_PROD {name} ({where}) -- defined and referenced nowhere in "
            f"the source tree{seen_in_tests}. If a contract relies on it, that "
            f"reliance has no executable closure.")

    return findings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether the test suite executes the production code it covers.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--source", default="scripts")
    parser.add_argument("--tests", default="tests")
    parser.add_argument("--entry-point", action="append", default=["main"])
    parser.add_argument("--ignore", action="append", default=[],
                        help="Symbol to exempt, with a reason recorded in the caller's notes.")
    parser.add_argument("--only", action="append", default=[],
                        help="Report findings whose path contains this substring. The whole "
                             "source tree is still analysed -- scoping the REPORT is safe, "
                             "scoping the analysis would make cross-module calls look dead.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo = args.repo.resolve()
    findings = audit(repo / args.source, repo / args.tests,
                     set(args.entry_point), set(args.ignore))
    if args.only:
        findings = [f for f in findings if any(token in f for token in args.only)]
    if findings:
        for finding in findings:
            print(f"FINDING {finding}", file=sys.stderr)
        print(f"\n{len(findings)} finding(s). A pass count does not see any of these.",
              file=sys.stderr)
        return 1
    print("TEST_REALITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
