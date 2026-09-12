# Native WSL environments

The 2026-09-12 infrastructure migration rebuilt two isolated Linux environments
from the installed Windows Python-distribution inventories. Research remains paused.
These records do not change frozen host/device requirements or authorize experiments.

| Purpose | Python | Local interpreter |
| --- | --- | --- |
| Lightweight control tools | 3.12.3 | `/home/fires/.venvs/hmasd-control/bin/python` |
| Local CPU imports and short assigned engineering checks | 3.10.20 | `/home/fires/.venvs/hmasd-linux-cpu/bin/python` |
| Scientific analysis tools declared in the capability catalog | 3.11.16 | `/home/fires/.venvs/hmasd-linux-science-tools/bin/python` |

The control environment has pytest/jsonschema and no torch. The CPU environment
has 90 distributions, including PyTorch 2.7.0+cpu, NumPy 1.26.3 and Ninja 1.13.0.
The analysis environment has 37 distributions; it remains separate from PyTorch.
The existing `hmasd-science-tools/` conda manifest and win-64 lock are preserved.

## Use

From the assigned native checkout, activate the required environment or call its
interpreter explicitly. For a native C++ loader, activation also exposes its Ninja:

```bash
source /home/fires/.venvs/hmasd-linux-cpu/bin/activate
python --version
# Use the already assigned check and invocation-owned scratch from tests/AGENTS.md.
```

For headless analysis, use `MPLBACKEND=Agg` with the analysis interpreter. Select
`local_linux_cpu` explicitly only for an assigned local check or an already authorized
portable fallback; `wsl_4070` remains the default result/heavy-compute node. Source
revision, admission and frozen card constraints still determine a valid invocation.

## Recreate in new, empty prefixes

Run these commands from the native checkout. Substitute new empty prefixes when
verifying recreation; do not overwrite or upgrade an environment in use. The recorded
installer is `/home/fires/.local/bin/uv` 0.12.5. No conda directory is copied across OSes.

```bash
/home/fires/.local/bin/uv python install 3.10.20 3.11.16 --no-bin
hmasd_cpu_prefix=/home/fires/.venvs/hmasd-linux-cpu
/home/fires/.local/bin/uv venv --python 3.10.20 "$hmasd_cpu_prefix"
/home/fires/.local/bin/uv pip install --python "$hmasd_cpu_prefix/bin/python" --no-deps \
  -r environments/hmasd-linux-cpu/requirements-pytorch-cpu.txt
/home/fires/.local/bin/uv pip install --python "$hmasd_cpu_prefix/bin/python" --no-deps \
  -r environments/hmasd-linux-cpu/requirements.txt
/home/fires/.local/bin/uv pip check --python "$hmasd_cpu_prefix/bin/python"

hmasd_analysis_prefix=/home/fires/.venvs/hmasd-linux-science-tools
/home/fires/.local/bin/uv venv --python 3.11.16 "$hmasd_analysis_prefix"
/home/fires/.local/bin/uv pip install --python "$hmasd_analysis_prefix/bin/python" --no-deps \
  -r environments/hmasd-linux-science-tools/requirements.txt
/home/fires/.local/bin/uv pip check --python "$hmasd_analysis_prefix/bin/python"
```

Exact versions cover the complete installed Python-distribution inventories, not
all conda/system binary artifacts. CPU excludes Windows-only `pywin32`; the torch
trio uses explicit Linux `+cpu` builds. Analysis excludes the source conda MKL Python
wrappers (`mkl-service`, `mkl_fft`, `mkl_random`) and unused Qt GUI bindings (`PyQt6`,
`PyQt6_sip`, `sip`). Linux wheels supply their supported native dependencies. Compiler,
BLAS, wheel build and platform differences do not establish numerical equivalence.

## Verified boundaries

Both new environments passed exact version reconciliation, declared public imports
and `uv pip check`. On native main at `db44de0134e7f33c4e60f420f1af683a3508caa0`, two
existing CPU loader tests compiled and loaded the source-keyed extension with GCC/G++
13.3.0 and Ninja, then verified source staging and module reuse (2 passed; one build
worker; 7.645 s total). Their scratch was removed. This is a local toolchain check,
not acceptance of every worktree's scientific source or cross-platform bit identity.

Node 24.20.0 and Git 2.43.0 run natively. Windows Codex Desktop and Agentify retain
their Windows executables and path conversion at the interface. External literature
libraries remain under `/mnt/c/Projects/`. Remote `/home/wu/` Python/GPU/supervisor,
existing live processes, original Windows environments and shell profiles are unchanged.
No CMake install was needed by the verified PyTorch JIT loader.

Source and installed inventories, package omissions and version pin digests are in
each environment's manifest. Detailed local logs, download SHA-256 receipts and
system inventory are at
`/home/fires/migration-records/hmasd-wsl-20260912/astra-desktop-repair/environment-audit/`.
