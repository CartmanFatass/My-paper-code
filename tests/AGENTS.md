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
Pytest's cache provider is disabled. Use `--keep-scratch-on-failure` when failed-test or
collection diagnostics must survive teardown; the invocation reports its retained path.
Success still cleans up. Tests may instead save selected diagnostics outside scratch before
teardown; do not treat temporary output as the only scientific evidence.

Review reproductions use this same lifecycle, including temporary Git repositories and copied
read-only fixtures. Put all generated files below `tmp_path` / `tmp_path_factory`, and wait
for fixture subprocesses before the test returns. Reuse an existing regression when it covers
the question; an assigning writer adds a needed new reproduction to the relevant test file.
A read-only reviewer does not create a standalone `temp/scratch-review-*` directory or edit
test sources. Existing checks run only where the runtime permits their scratch writes.
For example, the tracked-file case-alias regression can be run directly:

```powershell
python -m pytest -q tests/test_scratch_lifecycle.py -k mixed_case --keep-scratch-on-failure
```

Normal teardown is already the cleanup entrypoint. Use the recovery script below only for
known owned leftovers. New reproductions continue to use pytest-managed scratch.

A hard process kill or machine crash cannot run teardown. At the end of test work, after
all pytest processes have exited, use the fixed recovery command for any leftovers:

```powershell
# Preview completed-test scratch under temp/tests/.
./scripts/cleanup_test_scratch.ps1
# Reclaim only an explicitly identified owned invocation after checking the preview.
./scripts/cleanup_test_scratch.ps1 -RunDirectory temp/tests/<invocation> -Delete
# Direction-specific test scratch is also supported.
./scripts/cleanup_test_scratch.ps1 -RunDirectory temp/directions/<direction>/test/<tag> -Delete
# An old review fixture requires explicit mode AND a caller-verified exact target.
# Verify its creation history, contents and inactivity; its name alone proves no ownership.
./scripts/cleanup_test_scratch.ps1 -ReviewFixture -RunDirectory temp/scratch-review-<id>
./scripts/cleanup_test_scratch.ps1 -ReviewFixture -RunDirectory temp/scratch-review-<id> -Delete
```

Ordinary pytest teardown remains automatic; this command is the fallback for interrupted
sessions and verified owned leftovers; a name or age alone does not establish ownership.
Deletion requires explicit targets. Missing targets return AlreadyAbsent; every target reports
its outcome, and any refusal/incomplete deletion makes the command fail. It validates the
selected directories, refuses tracked content and links/junctions and checks native pytest processes.
Do not run it concurrently with test startup. It does not sweep experiment outputs or the
whole temp tree, kill processes, change ACLs or install a scheduled service. On non-Windows
hosts, normal pytest teardown still works; this recovery script is for Windows.
A tool-policy rejection must still be reported; a script is not a permission bypass.
The ReviewFixture mode only adds explicit single-directory recovery under the old
`temp/scratch-review-*` layout; it retains all existing safety checks and never enumerates
those directories for automatic deletion. It does not grant an exception to platform policy.

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
