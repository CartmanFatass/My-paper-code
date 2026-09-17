# tests/

Scientific tests use `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (Python 3.10,
torch 2.7.0+cpu, pytest 9). Control-plane skill tests that import `tomllib` use an existing
Python 3.11+ interpreter; the system `python` provides it but has no torch. Choose the
interpreter for the tested surface without installing into either conda environment.

## Layout

```
tests/<name>_test.py                                    core-tier tests (107 files; existing convention, kept)
tests/<package>/test_<subject>.py                       new core-tier tests mirror the source path
tests/experiments/candidates/<direction-id>/<attempt>/  research-tier tests, mirroring experiments/ exactly
tests/skills/                                           control-plane skill tests
tests/fixtures/<set>/                                   fixtures; hmasd_external_review and hmasd_science are eol=lf pinned
```

One naming convention for new files: `test_<subject>.py`. Existing `*_test.py` files stay; pytest
collects both (`pytest.ini`). Two flattened research test directories exist from before this rule
(`capability_bound_semantic_currentness_omrc_b01`, `..._online`); they are not renamed.

`tests/conftest.py` manages per-invocation scratch. Nested conftest files may provide
local scientific fixtures. No lint, format, or type tooling is configured.

## Commands and scratch

```powershell
# Scientific test: default scratch is allocated automatically under temp/tests/.
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q tests/hmasd_run_test.py
# Control-plane tests use Python 3.11+.
& 'C:/Users/fires/.conda/envs/hmasd-science-tools/python.exe' -m pytest -q tests/skills/
# Optional direction-specific location: use a fresh, nonexistent invocation directory.
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q --basetemp temp/directions/<direction>/test/<unique-tag> <paths>
```

The session allocates a unique directory under this checkout's `temp/tests/` unless an
explicit `--basetemp` is supplied. Explicit paths must be new directories inside `temp/`;
existing directories and redirected roots are refused before pytest can erase them.
Use `tmp_path` / `tmp_path_factory` for generated test files. The session removes only its
own directory on normal teardown, including failed tests and collection errors. Copied
Windows read-only attributes are cleared only in those test copies; source permissions
are unchanged. Cleanup failures report the exact path and error rather than disappearing.
Pytest's cache provider is disabled. Retain needed failure diagnostics outside scratch
before teardown; do not treat temporary output as the only scientific evidence.

A hard process kill or machine crash cannot run teardown. Leftovers from such interruptions
need explicit inspection and cleanup; no later test session sweeps old or other sessions'
directories. A tool-policy rejection is separate from filesystem permissions and must be
reported, not bypassed through another tool or interpreter.

## What tests are for here

Research tier (method: hmasd-research-engineering): a proportionate focused check
of changed behavior and primary output, plus rule tests when the object has branch rules.
Reuse existing checks for unchanged paths; a launch boundary alone does not require another
smoke test. Let coverage and changed risk determine the checks; report actual cost and coverage
gaps without a fixed test-duration or test-count ceiling.

Core tier: focused checks that would fail if the protected semantics (route, checkpoint
format, RNG stream, numerical result) changed. Bitwise claims are pinned by an off-path identity
test (the D2 `off` path is the example).

A test's relevance is judged against the declared execution node and supported topology.
