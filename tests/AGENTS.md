# tests/

Scientific tests use Python 3.10 with torch 2.7.0+cpu and pytest 9. Control-plane skill tests
that import `tomllib` use an existing Python 3.11+ interpreter, which has no torch. Choose the
interpreter for the tested surface, by host, and install into none of them. The current host
paths come from `.codex/hmasd-compute.toml` via `tools/research_support/interpreters.py`;
`HMASD_SCIENTIFIC_PYTHON` / `HMASD_CONTROL_PLANE_PYTHON` override them. On Linux the venv's `bin`
must be on `PATH` for any test that builds the native C++ geometry backend: `ninja` lives in the
venv and `torch.utils.cpp_extension` looks for it on `PATH`. Without it,
`tests/envs/uav_service_restoration` fails one test with "Ninja is required to load C++
extensions"; with it, that suite is 255 passed on both hosts.

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
# Windows. Run from the checkout root; py -3.11 only resolves the configured paths.
$scientific = py -3.11 -c 'from tools.research_support.interpreters import scientific_interpreter; print(scientific_interpreter())'
$controlPlane = py -3.11 -c 'from tools.research_support.interpreters import control_plane_interpreter; print(control_plane_interpreter())'
# Default scratch is allocated automatically under temp/tests/.
& $scientific -m pytest -q tests/hmasd_run_test.py
& $controlPlane -m pytest -q tests/skills/
# Optional direction-specific location: use a fresh, nonexistent invocation directory.
& $scientific -m pytest -q --basetemp temp/directions/<direction>/test/<unique-tag> <paths>
```

```bash
# WSL2. Run from the checkout root; python3 only resolves the configured paths.
scientific=$(python3 -c 'from tools.research_support.interpreters import scientific_interpreter; print(scientific_interpreter())')
control_plane=$(python3 -c 'from tools.research_support.interpreters import control_plane_interpreter; print(control_plane_interpreter())')
# PATH carries the venv's bin so the native C++ loader can find ninja.
PATH="$(dirname "$scientific"):$PATH" "$scientific" -m pytest -q tests/hmasd_run_test.py
"$control_plane" -m pytest -q tests/skills/
# Optional direction-specific location: use a fresh, nonexistent invocation directory.
PATH="$(dirname "$scientific"):$PATH" "$scientific" -m pytest -q --basetemp temp/directions/<direction>/test/<unique-tag> <paths>
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

That regression needs a case-insensitive filesystem: on Linux it skips, so a green run there
is not evidence about it.

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
hosts, normal pytest teardown still works; this recovery script is for Windows, and no
equivalent exists there: report an interrupted session's leftovers instead of sweeping them.
A tool-policy rejection must still be reported; a script is not a permission bypass.
Report the actual rejected invocation and its stated reason. A generic rejection alone does
not establish a target-wide deletion ban; consult the engineering skill's Stops guidance to
distinguish policy evidence, uncertain interpretation and a permitted safer implementation.
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
