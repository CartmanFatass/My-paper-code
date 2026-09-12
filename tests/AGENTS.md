# tests/

WSL control-plane tests use `/home/fires/.venvs/hmasd-control/bin/python`
(Python 3.12, pytest and jsonschema; no torch). Scientific tests use the interpreter on the
assigned execution node in `.codex/hmasd-compute.toml`; the remote node is the default for
committed portable heavy checks. The preserved Windows CPU environment is a Windows-only
fallback, not the default local WSL interpreter. Keep the assigned device and frozen versions.

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

```bash
# From the current native checkout; replace <run-tag> with this invocation's unique tag.
/home/fires/.venvs/hmasd-control/bin/python -m pytest -q \
  --basetemp temp/tests/<run-tag> tests/hmasd_run_test.py::test_name
# Scientific checks: run on the assigned node with its declared Python and source checkout.
python -m pytest -q --basetemp temp/directions/ucope/test/<run-tag> tests/experiments/candidates/ucope/
```

Every invocation supplies its own `--basetemp`: research tests use
`temp/directions/<direction-id>/test/<run-tag>`, other tests use `temp/tests/<run-tag>`.
All other generated test files also stay under that invocation's scratch directory.
Choose a unique run tag when tests may overlap. Pytest's cache provider is disabled
by default; test results belong in the existing acceptance record, not a retained cache.

The creating agent/process cleans its directory on completion, on success or failure,
using `finally` or an equivalent teardown. Before cleanup, retain only the result or
diagnostic evidence needed by the assignment. Confirm the resolved target is the exact
invocation directory under this checkout's `temp/`, then remove it; never clean the
shared `temp/` or another invocation's directory. After an interrupted process, its
creating agent performs the same cleanup before declaring the task complete.

## What tests are for here

Research tier (`docs/project/ENGINEERING_SCOPE_SPEC.md` §3–§5): a proportionate focused check
of changed behavior and primary output, plus rule tests when the object has branch rules.
Reuse existing checks for unchanged paths; a launch boundary alone does not require another
smoke test. Total wall time per research directory stays under 5 minutes excluding runner smoke.

Core tier: the one focused test that would fail if the changed semantic (route, checkpoint
format, RNG stream, numerical result) changed. Bitwise claims are pinned by an off-path identity
test (the D2 `off` path is the example).

A test's relevance is judged against the declared execution node and supported topology.
