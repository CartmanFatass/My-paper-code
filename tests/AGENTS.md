# tests/

Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (Python 3.10, torch 2.7.0+cpu,
pytest 9). The `python` on PATH is a bare system Python without torch. Never install into either
conda environment.

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

`conftest.py` exists only under `finite_resource_relational_inductive_efficiency/` (fixtures
only). No lint, format, or type tooling is configured; do not add any.

## Commands

```powershell
# one research directory
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/ucope/
# one file or one test
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/hmasd_run_test.py::test_name
# evidence-bearing run: isolate the temp dir under the direction's scratch root
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider `
  --basetemp C:/Projects/HMASD/temp/directions/<direction-id>/test/<run-tag> <paths>
```

`--basetemp` is always under `temp/directions/<direction-id>/test/`; the flat `temp/pytest-<slug>`
and root `.tmp_pytest_*` forms are retired.

## What tests are for here

Research tier (`docs/project/ENGINEERING_SCOPE_SPEC.md` §3–§5): one smoke test that runs the
runner end to end at toy size in under 60 seconds, plus rule tests pinning the mapping from
numbers to result branches. Total wall time per research directory under 5 minutes excluding the
runner smoke. Tests run once after an edit and once before a launch, not per slice or phase.

Core tier: the one focused test that would fail if the changed semantic (route, checkpoint
format, RNG stream, numerical result) changed. Bitwise claims are pinned by an off-path identity
test (the D2 `off` path is the example).

A test for a condition that cannot occur on this machine is deleted, not fixed.
