"""Change-aware test recommendation and failure classification (plan sections 12.1, 12.2).

Why this module exists: after a patch, the honest question is "which *existing* tests in this
repository actually exercise what changed, and with which interpreter". Answering it by hand is
slow and answering it by running the whole suite is expensive, so this module reads a Git diff and
proposes an explicit, reasoned subset. Three properties matter more than recall:

1. **It recommends only tests that exist.** Every recommendation is a real collectible file
   (``test_*.py`` or ``*_test.py``, matching ``pytest.ini``), resolved against the working tree.
2. **It never claims coverage.** A recommendation carries a confidence label and a reason, and
   everything the analysis cannot see (dynamic imports, compiled C++ kernels, contracts that only
   break across routes) is reported in :attr:`RecommendationReport.unresolved_coverage`. A passing
   subset is not evidence that a patch is safe, and no function here returns such a verdict.
3. **It does not act on its own.** Git is only ever invoked with a read-only subcommand allow-list
   and an argument array; :func:`run_recommended` executes only the paths the caller selected, via
   the normal pytest mechanism, and never installs anything.

Failure classification (plan section 12.2) lives here rather than in ``failure_bundle`` because its
input is pytest process output, which is produced here by :func:`run_recommended`.
``failure_bundle`` deliberately does not import this module: it must stay importable inside a
scientific process. ``context_bundle`` imports both.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import functools
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence

from .interpreters import control_plane_interpreter, scientific_interpreter

# --------------------------------------------------------------------------------------
# Interpreters (tests/AGENTS.md)
# --------------------------------------------------------------------------------------

#: Scientific surfaces: Python 3.10 with torch. Never install into it.
#: Resolved for the running host — see ``interpreters.py``; a recommended command has to
#: be runnable on the host that reads it, and a Windows path is not runnable from WSL.
SCIENTIFIC_INTERPRETER = scientific_interpreter()

#: Control-plane surfaces: Python 3.11+ (``tomllib``), no torch.
CONTROL_PLANE_INTERPRETER = control_plane_interpreter()

#: Test path prefixes that must run on the 3.11+ interpreter, per ``tests/AGENTS.md``.
CONTROL_PLANE_TEST_PREFIXES = ("tests/skills/",)

#: Files pytest collects here, from ``pytest.ini`` (``python_files = test_*.py *_test.py``).
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py")


def interpreter_for_test(test_path: str) -> str:
    """Resolve the interpreter a given test path must run under.

    ``tests/AGENTS.md`` states the rule the repository actually follows: control-plane skill tests
    import ``tomllib`` and therefore need Python 3.11+, everything else is scientific and runs on
    the torch-carrying 3.10 environment. The choice is made from the path because that is the only
    evidence available before the test is read.
    """

    posix = test_path.replace("\\", "/").lstrip("./")
    for prefix in CONTROL_PLANE_TEST_PREFIXES:
        if posix.startswith(prefix):
            return CONTROL_PLANE_INTERPRETER
    return SCIENTIFIC_INTERPRETER


# --------------------------------------------------------------------------------------
# Read-only Git access
# --------------------------------------------------------------------------------------


class GitCommandRefused(RuntimeError):
    """Raised when a caller asks for a Git subcommand this module refuses to run."""


class RecommendationError(RuntimeError):
    """Raised when the diff cannot be resolved; carries the exact failing command."""


#: The only Git subcommands this module will execute. Every one of them is read-only: none of
#: them writes the object database, the index, the working tree or a ref. This matters because the
#: repository checkout can be shared with other writers at any moment.
READ_ONLY_GIT_SUBCOMMANDS = frozenset(
    {"diff", "rev-parse", "show", "log", "cat-file", "ls-files", "ls-tree", "status"}
)


@dataclass(frozen=True)
class GitResult:
    """One executed Git command, kept with its exact argument array and exit code."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_json(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "returncode": int(self.returncode),
            "stderr": self.stderr.strip(),
        }


def run_read_only_git(
    repo: Path,
    arguments: Sequence[str],
    *,
    timeout_s: float = 60.0,
) -> GitResult:
    """Run one read-only Git command against ``repo`` using an argument array.

    There is no shell and no string interpolation: a branch or path containing a space, a quote or
    a semicolon is passed through as one argument. ``GIT_OPTIONAL_LOCKS=0`` stops Git from
    refreshing (and therefore locking) the index of a checkout another process may be using.
    """

    if not arguments:
        raise GitCommandRefused("no git subcommand given")
    subcommand = arguments[0]
    if subcommand not in READ_ONLY_GIT_SUBCOMMANDS:
        raise GitCommandRefused(
            f"git subcommand {subcommand!r} is not in the read-only allow-list "
            f"{sorted(READ_ONLY_GIT_SUBCOMMANDS)}"
        )
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    command = ("git", "-C", str(repo), "--no-pager", *arguments)
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RecommendationError(f"{' '.join(command)} failed: {exc}") from exc
    return GitResult(
        command=command,
        returncode=int(completed.returncode),
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


# --------------------------------------------------------------------------------------
# The explicit source -> test mapping table
# --------------------------------------------------------------------------------------


def _glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Compile a path glob where ``*`` stops at a separator and ``**`` crosses them.

    :func:`fnmatch.fnmatch` lets ``*`` match ``/``, which would make ``envs/*.py`` claim
    ``envs/pettingzoo/uav_cpp_backend.py`` and recommend the wrong tests. Mapping precision is the
    whole point of an explicit table, so the table uses these stricter semantics.
    """

    out: list[str] = []
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        if pattern.startswith("**", index):
            out.append(".*")
            index += 2
            continue
        if character == "*":
            out.append("[^/]*")
        elif character == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(character))
        index += 1
    return re.compile("".join(out) + r"\Z")


@functools.lru_cache(maxsize=512)
def _compiled_glob(pattern: str) -> "re.Pattern[str]":
    return _glob_to_regex(pattern)


def path_matches(path: str, pattern: str) -> bool:
    """True when the repository-relative POSIX ``path`` matches a table ``pattern``."""

    return _compiled_glob(pattern).match(path.replace("\\", "/")) is not None


@dataclass(frozen=True)
class SourceMapping:
    """One deliberate "this source is covered by those tests" statement.

    ``source_glob`` is matched with :func:`path_matches` against the repository-relative POSIX
    path of a changed file. ``test_globs`` are repository-relative glob patterns expanded against
    the working tree, so a pattern that no longer matches any file simply contributes nothing
    instead of recommending a test that does not exist. ``{stem}`` in a test glob is replaced by
    the changed file's stem.
    """

    source_glob: str
    test_globs: tuple[str, ...]
    reason: str
    interpreter: str | None = None
    external_artifacts: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()


#: Mapping table for this repository's real layout. Order matters only for readability; every
#: matching entry contributes. Entries were checked against the working tree: each ``test_globs``
#: pattern matches at least one existing test file at the time of writing.
SOURCE_TEST_MAPPINGS: tuple[SourceMapping, ...] = (
    SourceMapping(
        source_glob="ha_ctse_process/standalone_low_update.py",
        test_globs=(
            "tests/**/*truncation*_test.py",
            "tests/**/*low_update*_test.py",
            "tests/**/test_*truncation*.py",
            "tests/**/test_*low_update*.py",
        ),
        reason="low-level update path: truncation/GAE boundary tests",
    ),
    SourceMapping(
        source_glob="ha_ctse_process/standalone_*.py",
        test_globs=("tests/process/standalone/*_test.py",),
        reason="standalone process family shares the tests/process/standalone suite",
    ),
    SourceMapping(
        source_glob="ha_ctse_process/*variable_roster*.py",
        test_globs=("tests/process/variable_roster/*_test.py",),
        reason="variable-roster process family",
    ),
    SourceMapping(
        source_glob="ha_ctse_process/*roster*.py",
        test_globs=("tests/process/variable_roster/*_test.py",),
        reason="roster process family",
    ),
    SourceMapping(
        source_glob="ha_ctse_process/*.py",
        test_globs=("tests/ha_ctse_process_*{stem}*_test.py", "tests/run_*{stem}*_test.py"),
        reason="ha_ctse_process module has a same-named core-tier test",
    ),
    SourceMapping(
        source_glob="envs/uav_service_restoration/*.py",
        test_globs=(
            "tests/envs/uav_service_restoration/test_*.py",
            "tests/uav_service_restoration*_test.py",
            "tests/**/test_*service_restoration*.py",
        ),
        reason="UAV service-restoration environment package",
        unresolved=(
            "envs/uav_service_restoration: adapter/scheduler contracts are also exercised by "
            "route integrations outside this package",
        ),
    ),
    SourceMapping(
        source_glob="envs/uav_service_restoration/preprocess_milan.py",
        test_globs=("tests/envs/uav_service_restoration/test_milan_preprocess.py",),
        reason="Milan demand preprocessing",
        external_artifacts=("Milan telecom demand source files at the configured dataset path",),
    ),
    SourceMapping(
        source_glob="envs/uav_service_restoration/demand.py",
        test_globs=(
            "tests/envs/uav_service_restoration/test_demand_sources.py",
            "tests/envs/uav_service_restoration/test_milan_preprocess.py",
        ),
        reason="demand sources read prepared dataset artifacts",
        external_artifacts=("prepared demand dataset artifacts",),
    ),
    SourceMapping(
        source_glob="envs/pettingzoo/uav_cpp_backend.py",
        test_globs=("tests/uav_cpp_backend*_test.py", "tests/uav_env_channel_equivalence_test.py"),
        reason="UAV C++ backend loader",
        external_artifacts=("compiled torch cpp_extension build cache and a C++ toolchain",),
        unresolved=(
            "envs/pettingzoo/uav_cpp_backend.py: the compiled kernel itself is not covered by "
            "Python tests; only the loader and the Python-side equivalence checks are",
        ),
    ),
    SourceMapping(
        source_glob="envs/continuous_roster/cpp_backend.py",
        test_globs=(
            "tests/*cpp_backend*_test.py",
            "tests/ha_ctse_process_continuous_roster_toy_cpp_backend_test.py",
        ),
        reason="continuous-roster C++ backend loader",
        external_artifacts=("compiled torch cpp_extension build cache and a C++ toolchain",),
        unresolved=(
            "envs/continuous_roster/cpp_backend.py: compiled kernel behaviour is not covered by "
            "the Python tests",
        ),
    ),
    SourceMapping(
        source_glob="envs/native/*.py",
        test_globs=("tests/production_backend_policy_test.py", "tests/*cpp_backend*_test.py"),
        reason="native backend loading/policy surface",
        external_artifacts=("compiled extension cache under the configured build root",),
        unresolved=(
            "envs/native: extension build/caching depends on the local compiler toolchain, which "
            "the recommended Python tests only partly exercise",
        ),
    ),
    SourceMapping(
        source_glob="envs/pettingzoo/uav_env.py",
        test_globs=("tests/uav_*_test.py",),
        reason="UAV environment surface",
    ),
    SourceMapping(
        source_glob="envs/pettingzoo/scenario*.py",
        test_globs=("tests/scenario*_test.py",),
        reason="scenario environment family",
    ),
    SourceMapping(
        source_glob="envs/relay_corridor/*.py",
        test_globs=("tests/relay_*_test.py",),
        reason="relay corridor host/driver",
    ),
    SourceMapping(
        source_glob="envs/*.py",
        test_globs=("tests/hmasd_science_environment_test.py",),
        reason="shared environment entry points",
    ),
    SourceMapping(
        source_glob="hmasd/*.py",
        test_globs=("tests/hmasd_*{stem}*_test.py", "tests/hmasd_*_test.py"),
        reason="core learner package",
        unresolved=(
            "hmasd: learner changes can alter checkpoint compatibility and RNG stream order, "
            "which a recommended subset does not prove",
        ),
    ),
    SourceMapping(
        source_glob="tools/research_support/**",
        test_globs=("tests/tools/research_support/test_*.py",),
        reason="research support suite mirrors its tests under tests/tools/research_support",
    ),
    SourceMapping(
        source_glob="tools/owner_console/**",
        test_globs=("tests/tools/owner_console/test_*.py",),
        reason="owner console tool",
    ),
    SourceMapping(
        source_glob="tools/model_comparison/**",
        test_globs=("tests/tools/model_comparison/test_*.py",),
        reason="model comparison tool",
    ),
    SourceMapping(
        source_glob="tools/publish_claude_control.py",
        test_globs=("tests/skills/test_control_publication.py", "tests/skills/test_control_alignment.py"),
        reason="control-plane publication tool",
        interpreter=CONTROL_PLANE_INTERPRETER,
    ),
    SourceMapping(
        source_glob=".agents/skills/**",
        test_globs=("tests/skills/test_*.py",),
        reason="control-plane method text is checked by the skill tests",
        interpreter=CONTROL_PLANE_INTERPRETER,
    ),
    SourceMapping(
        source_glob=".claude/**",
        test_globs=("tests/skills/test_control_alignment.py", "tests/skills/test_control_publication.py"),
        reason="generated Claude control copies are checked against their sources",
        interpreter=CONTROL_PLANE_INTERPRETER,
    ),
    SourceMapping(
        source_glob="scripts/hmasd_launch.py",
        test_globs=(
            "tests/test_hmasd_launch.py",
            "tests/test_runner_admission_contract.py",
            "tests/test_hmasd_source_snapshot.py",
        ),
        reason="launch script and its admission guard",
    ),
    SourceMapping(
        source_glob="tests/conftest.py",
        test_globs=("tests/test_scratch_lifecycle.py",),
        reason="scratch lifecycle is owned by the root conftest",
    ),
    SourceMapping(
        source_glob="experiments/**/*.py",
        test_globs=("tests/experiments/**/test_*.py", "tests/experiments/**/*_test.py"),
        reason="research-tier tests mirror experiments/ exactly",
    ),
)


# --------------------------------------------------------------------------------------
# Unresolved coverage triggers
# --------------------------------------------------------------------------------------

#: Changed paths that Python tests cannot fully cover, whatever the recommendation says.
NATIVE_PATH_PATTERNS = (
    "envs/native/**",
    "envs/pettingzoo/uav_cpp_backend.py",
    "envs/continuous_roster/cpp_backend.py",
    "**/native/**",
    "**/*.cpp",
    "**/*.cc",
    "**/*.cu",
    "**/*.h",
    "**/*.hpp",
    "**/*.pyx",
)

#: Source text that means "the import graph this module reads is not the whole truth".
DYNAMIC_IMPORT_MARKERS = (
    "importlib",
    "__import__",
    "spec_from_file_location",
    "exec_module",
)


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TestRecommendation:
    """One existing test proposed for one reason, with the interpreter it must run under."""

    test_path: str
    reason: str
    interpreter: str
    confidence: str  # "direct_mapping" | "import_dependency" | "heuristic"
    external_artifacts: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "test_path": self.test_path,
            "reason": self.reason,
            "interpreter": self.interpreter,
            "confidence": self.confidence,
            "external_artifacts": list(self.external_artifacts),
            "command": list(pytest_command(self.test_path, interpreter=self.interpreter)),
        }


#: Confidence ordering, strongest first. Used to keep the best reason for a test recommended twice.
CONFIDENCE_ORDER = ("direct_mapping", "import_dependency", "heuristic")


@dataclass
class RecommendationReport:
    """What the diff changed, what to run, and what nobody has covered."""

    base: str
    head: str
    changed_files: list[str]
    recommendations: list[TestRecommendation]
    unresolved_coverage: list[str]
    notes: list[str]
    #: Added field (not in the minimal contract): the exact Git commands and their exit codes, so
    #: a reader can reproduce the diff resolution instead of trusting this report's file list.
    git_commands: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "head": self.head,
            "changed_files": list(self.changed_files),
            "recommendations": [r.to_json() for r in self.recommendations],
            "unresolved_coverage": list(self.unresolved_coverage),
            "notes": list(self.notes),
            "git_commands": [dict(c) for c in self.git_commands],
            "coverage_claim": (
                "none: this is a recommendation, not a proof of coverage; a passing subset does "
                "not make a patch safe"
            ),
        }

    def selected_paths(self) -> set[str]:
        return {r.test_path for r in self.recommendations}


def pytest_command(test_path: str, *, interpreter: str | None = None) -> tuple[str, ...]:
    """The exact argument array used to run one recommended test."""

    resolved = interpreter or interpreter_for_test(test_path)
    return (resolved, "-m", "pytest", "-q", test_path)


# --------------------------------------------------------------------------------------
# Diff resolution
# --------------------------------------------------------------------------------------


def _resolve_commit(repo: Path, revision: str, commands: list[dict[str, Any]]) -> str:
    result = run_read_only_git(repo, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    commands.append(result.to_json())
    if not result.ok:
        raise RecommendationError(
            f"cannot resolve revision {revision!r}: {' '.join(result.command)} "
            f"exited {result.returncode}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _changed_files(repo: Path, base: str, head: str, commands: list[dict[str, Any]]) -> list[str]:
    result = run_read_only_git(repo, ["diff", "--name-only", f"{base}..{head}"])
    commands.append(result.to_json())
    if not result.ok:
        raise RecommendationError(
            f"cannot diff {base}..{head}: {' '.join(result.command)} "
            f"exited {result.returncode}: {result.stderr.strip()}"
        )
    return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})


# --------------------------------------------------------------------------------------
# Bounded static import analysis
# --------------------------------------------------------------------------------------


def _is_test_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in TEST_FILE_PATTERNS)


def _iter_test_files(repo: Path, *, cap: int) -> tuple[list[Path], bool]:
    """Every collectible test file under ``tests/``, capped. Returns (files, cap_hit)."""

    tests_root = repo / "tests"
    found: list[Path] = []
    if not tests_root.is_dir():
        return found, False
    for path in sorted(tests_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if not _is_test_file(path.name):
            continue
        found.append(path)
        if len(found) >= cap:
            return found, True
    return found, False


def _module_names_for(relative_path: str) -> set[str]:
    """Dotted module names a changed file can be imported under."""

    posix = relative_path.replace("\\", "/")
    if not posix.endswith(".py"):
        return set()
    parts = posix[:-3].split("/")
    names: set[str] = set()
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return names
    names.add(".".join(parts))
    # A test run from inside a package directory can import the module by its bare name.
    names.add(parts[-1])
    return names


def _parse_imports(path: Path) -> tuple[set[str], bool]:
    """Imported dotted names in one file, plus whether it performs dynamic imports.

    Relative imports are recorded as unresolved dynamic-ish evidence rather than guessed at: a
    test file almost never uses them, and a wrong resolution would be worse than a note.
    """

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set(), False
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return set(), False
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            module = node.module or ""
            if module:
                names.add(module)
                for alias in node.names:
                    names.add(f"{module}.{alias.name}")
    dynamic = any(marker in text for marker in DYNAMIC_IMPORT_MARKERS)
    return names, dynamic


def _module_file(repo: Path, module: str) -> Path | None:
    parts = module.split(".")
    candidate = repo.joinpath(*parts).with_suffix(".py")
    if candidate.is_file():
        return candidate
    package = repo.joinpath(*parts, "__init__.py")
    if package.is_file():
        return package
    return None


# --------------------------------------------------------------------------------------
# Recommendation
# --------------------------------------------------------------------------------------


def _expand_test_globs(repo: Path, patterns: Iterable[str], stem: str) -> list[str]:
    found: set[str] = set()
    for pattern in patterns:
        concrete = pattern.replace("{stem}", stem)
        for path in repo.glob(concrete):
            if not path.is_file() or not _is_test_file(path.name):
                continue
            found.add(path.relative_to(repo).as_posix())
    return sorted(found)


def _heuristic_tokens(stem: str) -> set[str]:
    return {token for token in stem.split("_") if len(token) >= 4}


def recommend_tests(
    repo: Path,
    *,
    base: str,
    head: str = "HEAD",
    max_test_files: int = 800,
    max_hop_modules: int = 400,
) -> RecommendationReport:
    """Read a Git diff and recommend existing tests, with reasons and unresolved coverage.

    The three strategies are applied in order and the strongest reason wins per test path:
    (1) the explicit :data:`SOURCE_TEST_MAPPINGS` table, (2) bounded static import analysis
    (direct import or one hop through a repository module), (3) a filename heuristic. Nothing is
    executed: this function only reads.
    """

    repo = Path(repo)
    commands: list[dict[str, Any]] = []
    notes: list[str] = []
    base_sha = _resolve_commit(repo, base, commands)
    head_sha = _resolve_commit(repo, head, commands)
    changed = _changed_files(repo, base_sha, head_sha, commands)
    notes.append("diff resolved with: " + " ".join(commands[-1]["command"]))

    best: dict[str, TestRecommendation] = {}
    unresolved: list[str] = []
    covered_sources: set[str] = set()

    def offer(recommendation: TestRecommendation) -> None:
        current = best.get(recommendation.test_path)
        if current is None:
            best[recommendation.test_path] = recommendation
            return
        if CONFIDENCE_ORDER.index(recommendation.confidence) < CONFIDENCE_ORDER.index(
            current.confidence
        ):
            merged_artifacts = tuple(
                sorted(set(recommendation.external_artifacts) | set(current.external_artifacts))
            )
            best[recommendation.test_path] = TestRecommendation(
                test_path=recommendation.test_path,
                reason=recommendation.reason,
                interpreter=recommendation.interpreter,
                confidence=recommendation.confidence,
                external_artifacts=merged_artifacts,
            )

    # ---- Strategy 1: explicit mapping table -------------------------------------------
    for changed_path in changed:
        posix = changed_path.replace("\\", "/")
        stem = Path(posix).stem
        for mapping in SOURCE_TEST_MAPPINGS:
            if not path_matches(posix, mapping.source_glob):
                continue
            for note in mapping.unresolved:
                if note not in unresolved:
                    unresolved.append(note)
            for test_path in _expand_test_globs(repo, mapping.test_globs, stem):
                covered_sources.add(posix)
                offer(
                    TestRecommendation(
                        test_path=test_path,
                        reason=f"{posix}: {mapping.reason} (mapping {mapping.source_glob})",
                        interpreter=mapping.interpreter or interpreter_for_test(test_path),
                        confidence="direct_mapping",
                        external_artifacts=mapping.external_artifacts,
                    )
                )

    # ---- Strategy 2: bounded static import analysis ------------------------------------
    changed_modules: dict[str, str] = {}
    for changed_path in changed:
        for module in _module_names_for(changed_path):
            changed_modules[module] = changed_path
    dynamic_sources: list[str] = []
    for changed_path in changed:
        source_file = repo / changed_path
        if source_file.is_file() and source_file.suffix == ".py":
            _, dynamic = _parse_imports(source_file)
            if dynamic:
                dynamic_sources.append(changed_path)

    test_files, cap_hit = _iter_test_files(repo, cap=max_test_files)
    notes.append(
        f"import analysis parsed {len(test_files)} test files (cap {max_test_files}"
        f"{', CAP REACHED: the search is incomplete' if cap_hit else ''})"
    )
    if cap_hit:
        unresolved.append(
            f"static import analysis stopped at the {max_test_files}-file cap; tests beyond the "
            "cap were never examined"
        )
    hop_cache: dict[str, set[str]] = {}
    hop_budget = max_hop_modules
    hop_cap_hit = False
    dynamic_tests: list[str] = []
    for test_file in test_files:
        test_rel = test_file.relative_to(repo).as_posix()
        imports, dynamic = _parse_imports(test_file)
        if dynamic:
            dynamic_tests.append(test_rel)
        hit = sorted(imports & set(changed_modules))
        if hit:
            module = hit[0]
            offer(
                TestRecommendation(
                    test_path=test_rel,
                    reason=(
                        f"imports {module} directly, which {changed_modules[module]} defines"
                    ),
                    interpreter=interpreter_for_test(test_rel),
                    confidence="import_dependency",
                )
            )
            covered_sources.add(changed_modules[module])
            continue
        # One hop: the test imports a repository module which imports a changed module.
        for module in sorted(imports):
            if module in hop_cache:
                hop_imports = hop_cache[module]
            else:
                if hop_budget <= 0:
                    hop_cap_hit = True
                    break
                module_file = _module_file(repo, module)
                if module_file is None:
                    hop_cache[module] = set()
                    continue
                hop_budget -= 1
                hop_imports, _ = _parse_imports(module_file)
                hop_cache[module] = hop_imports
            intermediate_hit = sorted(hop_imports & set(changed_modules))
            if intermediate_hit:
                changed_module = intermediate_hit[0]
                offer(
                    TestRecommendation(
                        test_path=test_rel,
                        reason=(
                            f"imports {module}, which imports {changed_module} from "
                            f"{changed_modules[changed_module]} (one hop)"
                        ),
                        interpreter=interpreter_for_test(test_rel),
                        confidence="import_dependency",
                    )
                )
                covered_sources.add(changed_modules[changed_module])
                break
    notes.append(
        f"one-hop module analysis parsed {max_hop_modules - hop_budget} modules "
        f"(cap {max_hop_modules}{', CAP REACHED' if hop_cap_hit else ''})"
    )
    if hop_cap_hit:
        unresolved.append(
            f"one-hop import analysis stopped at the {max_hop_modules}-module cap; deeper or "
            "later dependency edges were never examined"
        )

    # ---- Strategy 3: filename heuristic -------------------------------------------------
    for changed_path in changed:
        posix = changed_path.replace("\\", "/")
        if posix in covered_sources or not posix.endswith(".py"):
            continue
        stem = Path(posix).stem
        tokens = _heuristic_tokens(stem)
        if not tokens:
            continue
        for test_file in test_files:
            test_rel = test_file.relative_to(repo).as_posix()
            test_stem = test_file.stem
            shared = tokens & _heuristic_tokens(test_stem)
            if stem and stem in test_stem:
                reason = f"{posix}: test filename contains the changed module stem {stem!r}"
            elif len(shared) >= 2:
                reason = (
                    f"{posix}: test filename shares tokens {sorted(shared)} with the changed module"
                )
            else:
                continue
            covered_sources.add(posix)
            offer(
                TestRecommendation(
                    test_path=test_rel,
                    reason=reason,
                    interpreter=interpreter_for_test(test_rel),
                    confidence="heuristic",
                )
            )

    # ---- Unresolved coverage ------------------------------------------------------------
    for changed_path in changed:
        posix = changed_path.replace("\\", "/")
        if any(path_matches(posix, pattern) for pattern in NATIVE_PATH_PATTERNS):
            unresolved.append(
                f"{posix}: native/compiled kernel; the recommended Python tests cannot observe "
                "the compiled path itself"
            )
        if posix not in covered_sources:
            unresolved.append(
                f"{posix}: no mapped, imported or name-matching test was found; coverage for this "
                "change is unknown"
            )
    for path in dynamic_sources:
        unresolved.append(
            f"{path}: performs dynamic imports, so the static import graph used here is incomplete"
        )
    if dynamic_tests:
        unresolved.append(
            f"{len(set(dynamic_tests))} test files load modules dynamically (importlib/"
            "spec_from_file_location); their dependence on changed files is not visible to "
            "static analysis"
        )
    if any(
        changed_path.replace("\\", "/").startswith(("envs/", "hmasd/", "ha_ctse_process/"))
        for changed_path in changed
    ):
        unresolved.append(
            "cross-route contracts: a change under envs/, hmasd/ or ha_ctse_process/ can break a "
            "route whose tests are not in this subset"
        )

    notes.append(
        "a recommendation is not a proof of coverage: do not label a patch safe because the "
        "recommended subset passed"
    )
    notes.append(
        "interpreters are resolved per tests/AGENTS.md: tests/skills/ needs Python 3.11+ "
        f"({CONTROL_PLANE_INTERPRETER}); everything else uses {SCIENTIFIC_INTERPRETER}"
    )

    recommendations = sorted(
        best.values(),
        key=lambda r: (CONFIDENCE_ORDER.index(r.confidence), r.test_path),
    )
    return RecommendationReport(
        base=base_sha,
        head=head_sha,
        changed_files=changed,
        recommendations=recommendations,
        unresolved_coverage=list(dict.fromkeys(unresolved)),
        notes=notes,
        git_commands=commands,
    )


# --------------------------------------------------------------------------------------
# Failure classification (plan section 12.2)
# --------------------------------------------------------------------------------------


class FailureClass(str, Enum):
    """Why a test invocation failed, where the evidence supports saying so."""

    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    COLLECTION_ERROR = "COLLECTION_ERROR"
    MISSING_EXTERNAL_ARTIFACT = "MISSING_EXTERNAL_ARTIFACT"
    MISSING_OPTIONAL_DEPENDENCY = "MISSING_OPTIONAL_DEPENDENCY"
    UNSUPPORTED_RUNTIME = "UNSUPPORTED_RUNTIME"
    TOOL_PERMISSION_REFUSAL = "TOOL_PERMISSION_REFUSAL"
    UNCLASSIFIED = "UNCLASSIFIED"


#: Ordered (class, marker) rules. The first matching marker wins, so the more specific cause is
#: reported: "ImportError while importing test module ... No module named 'gymnasium'" is a missing
#: dependency, which is actionable, rather than a bare collection error, which is not.
_CLASSIFICATION_RULES: tuple[tuple[FailureClass, tuple[str, ...]], ...] = (
    (
        FailureClass.UNSUPPORTED_RUNTIME,
        (
            "no module named 'tomllib'",
            "requires python 3.",
            "unsupported python version",
            "unsupported platform",
            "torch not compiled with cuda",
            "cuda is not available",
            "is not supported on this platform",
        ),
    ),
    (
        FailureClass.MISSING_OPTIONAL_DEPENDENCY,
        (
            "modulenotfounderror: no module named",
            "importerror: no module named",
            "could not find a version that satisfies the requirement",
        ),
    ),
    (
        FailureClass.TOOL_PERMISSION_REFUSAL,
        (
            "permission denied",
            "access is denied",
            "permissionerror",
            "operation not permitted",
            "refused by tool policy",
            "tool policy refused",
            "requires approval",
        ),
    ),
    (
        FailureClass.MISSING_EXTERNAL_ARTIFACT,
        (
            "filenotfounderror",
            "no such file or directory",
            "checkpoint not found",
            "dataset not found",
            "missing artifact",
        ),
    ),
    (
        FailureClass.COLLECTION_ERROR,
        (
            "errors during collection",
            "error collecting",
            "importerror while importing test module",
            "internalerror",
            "usageerror",
        ),
    ),
    (
        FailureClass.ASSERTION_FAILURE,
        (
            "assertionerror",
            "= failures =",
            "failed ",
            "\nassert ",
            "e       assert",
        ),
    ),
)

#: How much raw tail text an UNCLASSIFIED verdict keeps inline. The caller keeps everything.
_UNCLASSIFIED_TAIL_CHARS = 2000


def classify_failure(stdout: str, stderr: str, returncode: int) -> tuple[FailureClass, str]:
    """Classify a test invocation's output, preserving the evidence verbatim.

    Classification never converts a failure into a success: a non-zero exit code whose text matches
    no rule is :attr:`FailureClass.UNCLASSIFIED` with the raw tail quoted, not a benign label. A
    zero exit code is likewise reported as ``UNCLASSIFIED`` with a statement that no failure was
    observed, because this function is not a pass/fail oracle.

    The returned detail names the matched marker and quotes the exact line it matched, so a reader
    can check the classification against the raw text the caller stores alongside it.
    """

    combined = f"{stdout}\n{stderr}"
    lowered = combined.lower()
    if int(returncode) == 0:
        return (
            FailureClass.UNCLASSIFIED,
            "exit status 0: no failure observed; this function classifies failures and does not "
            "certify success",
        )
    for failure_class, markers in _CLASSIFICATION_RULES:
        for marker in markers:
            index = lowered.find(marker)
            if index < 0:
                continue
            line_start = combined.rfind("\n", 0, index) + 1
            line_end = combined.find("\n", index)
            line = combined[line_start : line_end if line_end >= 0 else len(combined)]
            return (
                failure_class,
                f"exit {returncode}; matched marker {marker!r} in evidence line: {line.strip()}",
            )
    tail = combined.strip()[-_UNCLASSIFIED_TAIL_CHARS:]
    return (
        FailureClass.UNCLASSIFIED,
        f"exit {returncode}; no classification rule matched. Raw tail preserved verbatim:\n{tail}",
    )


# --------------------------------------------------------------------------------------
# Explicit execution of a caller-selected subset
# --------------------------------------------------------------------------------------


class SelectionRefused(ValueError):
    """Raised when a caller asks to run something the report did not recommend."""


def run_recommended(
    report: RecommendationReport,
    *,
    selected: Sequence[str],
    repo: Path,
    timeout_s: float = 1800.0,
) -> list[dict[str, Any]]:
    """Run exactly the selected recommended tests, one pytest invocation per path.

    Guarantees, in order of importance: only paths present in ``report`` run (so this can never
    become "run the whole suite"); every invocation is an argument array with the interpreter the
    report resolved; nothing is installed; raw stdout/stderr and the exit code are preserved
    verbatim next to the classification. ``timeout_s`` is a budget shared by the whole selection;
    a path that no longer has budget is reported as not run rather than silently skipped.
    """

    repo = Path(repo)
    known = {r.test_path: r for r in report.recommendations}
    for path in selected:
        if path not in known:
            raise SelectionRefused(
                f"{path!r} is not in this report's recommendations; run_recommended never expands "
                "the selection (and never runs the full suite)"
            )
    results: list[dict[str, Any]] = []
    deadline = time.monotonic() + float(timeout_s)
    for path in selected:
        recommendation = known[path]
        command = pytest_command(path, interpreter=recommendation.interpreter)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            results.append(
                {
                    "test_path": path,
                    "interpreter": recommendation.interpreter,
                    "command": list(command),
                    "returncode": None,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": False,
                    "executed": False,
                    "status": "not_run_time_budget_exhausted",
                    "failure_class": FailureClass.UNCLASSIFIED.value,
                    "failure_detail": "not executed: the shared time budget was exhausted",
                    "duration_s": 0.0,
                }
            )
            continue
        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(
                list(command),
                check=False,
                cwd=str(repo),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=remaining,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            returncode: int | None = int(completed.returncode)
            stdout, stderr = completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = None
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        except OSError as exc:
            returncode = None
            stdout, stderr = "", f"failed to start {command[0]}: {exc}"
        duration = time.monotonic() - started
        if timed_out:
            failure_class, detail = (
                FailureClass.UNCLASSIFIED,
                f"timed out after {duration:.1f}s; partial output preserved verbatim",
            )
        elif returncode is None:
            failure_class, detail = (
                FailureClass.UNCLASSIFIED,
                f"the interpreter could not be started: {stderr.strip()}",
            )
        else:
            failure_class, detail = classify_failure(stdout, stderr, returncode)
        results.append(
            {
                "test_path": path,
                "interpreter": recommendation.interpreter,
                "command": list(command),
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": timed_out,
                "executed": True,
                "status": "completed" if returncode is not None else "not_started",
                "failure_class": failure_class.value,
                "failure_detail": detail,
                "duration_s": round(duration, 3),
            }
        )
    return results


# --------------------------------------------------------------------------------------
# Command line (plan section 12.1: an explicit --run mode, never a default full-suite run)
# --------------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="recommend_tests",
        description=(
            "Recommend existing tests for a Git diff. Recommending is read-only; --run executes "
            "only the tests named with --select."
        ),
    )
    parser.add_argument("--repo", type=Path, required=True, help="repository to read")
    parser.add_argument("--base", required=True, help="base revision")
    parser.add_argument("--head", default="HEAD", help="head revision (default HEAD)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="execute the --select paths; without --select this does nothing",
    )
    parser.add_argument(
        "--select",
        action="append",
        default=[],
        metavar="TEST_PATH",
        help="a recommended test path to execute under --run; repeatable",
    )
    parser.add_argument("--timeout-s", type=float, default=1800.0)
    arguments = parser.parse_args(list(argv) if argv is not None else None)

    report = recommend_tests(arguments.repo, base=arguments.base, head=arguments.head)
    payload: dict[str, Any] = {"report": report.to_json()}
    if arguments.run and arguments.select:
        payload["results"] = run_recommended(
            report,
            selected=arguments.select,
            repo=arguments.repo,
            timeout_s=arguments.timeout_s,
        )
    elif arguments.run:
        payload["results"] = []
        payload["run_note"] = "--run without --select executes nothing by design"
    print(json.dumps(payload, indent=2))
    failed = any(
        result.get("returncode") not in (0, None) for result in payload.get("results", ())
    )
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - exercised through main(argv)
    sys.exit(main())
