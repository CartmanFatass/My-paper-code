# CBSC-SYSTEM-RUNTIME-A01 CM command and result record

## Selected work and source

Contract: [A01 card](CBSC_SYSTEM_RUNTIME_A01_SCIENCE_CARD_20260907.md), Question,
Selected path, Work/budget/execution, Reading rule; [selection](CBSC_SYSTEM_RUNTIME_A01_SELECTION_20260907.md),
Facts and decision value / Five-item CM handoff. Environment readiness only.
One candidate, one binary dependency installation, one metadata/import observation;
zero host tapes, scientific model/RNG calls, optimizers, training or evaluation.
No B04 retry, diagnosis, stability or numerical-equivalence claim is selected.

Own fresh branch `codex/cm-cbsc-runtime-a01-20260907`, local worktree
`C:/Projects/HMASD-worktrees/cm-cbsc-runtime-a01-20260907`, from pushed
`56edc4156235ff4121238ea2f083d90aca8787bf`. Initial Git state was clean.
Only this command/result record is added; no scientific source, shared environment,
configuration, system package or other direction environment is changed.
Engineering-scope section4 additions: none. Existing uv/package tools and a literal
command are used, without a new runner/framework/helper or child chain.

Selected environment `/home/wu/.venvs/hmasd-cbsc-system312-20260907` was absent
on the node at pre-acceptance path inspection. Existing `/usr/bin/python3` is
selected as the OS CPython3.12 source, without managed Python download. All candidate
invocations keep the lexical `.../bin/python` path; resolving its path is metadata
only. Binary pins are numpy==1.26.3 and torch==2.7.0+cu118 plus declared dependencies.
The official PyPI and PyTorch cu118 indexes are explicit. uv's best-match strategy
searches both official indexes for the exact pins and dependency closure; it does
not relax either pin. Binary-only applies to the full installation. Verbose install
log retains actual index/cache/wheel resolution facts; metadata records module and
distribution locations, versions, installer and available direct-url metadata.

## Frozen invocation

Node wsl_4070, SSH hmasd-wsl-node. Detached exact-command-SHA worktree:
`/home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907`.
Output root:
`/home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a01_20260907`.
Handle `cbsc-system-runtime-a01-20260907`. Source is this pushed command-record
commit; its resolved SHA will be recorded with the accepted handle. No uncommitted
source is copied. Git/network preparation uses the configured zsh login route.

The existing agent-task receives one quoted `bash -lc` invocation of the exact
command below. Outer GNU time and timeout enclose zsh login/network setup, fresh
system-Python memory admission joined by && to environment creation, install,
sole import/metadata query, JSON write/readback and termination. 598s timeout plus
2s kill grace stays inside the single600s allocation. No phase has a reset clock.
Time output is in the existing supervisor handle directory, created by agent-task.
Admission must pass actual-node physical/effective4GiB before candidate creation.
The metadata query imports libraries once and may set Torch threads1; it makes no
tensor/model/host call and writes/readbacks summary.json. A failure retains logs
and the partial candidate; no automatic restart, second candidate or source build.

Cost law: admission + venv creation + binary resolution/cache/download/unpack +
metadata imports + publication/readback + grace. No prior complete cost is measured;
network/package size and cache benefit remain unknown. This is one bounded setup,
not a sweep. Aggregate CPU and transfer volume are not claims. No standalone test
or smoke is selected, and the historical focused-test account is not reset.

Post-install publication is the literal JSON write/readback in the same sole import
observation. Failure before that point leaves no successful metadata result.
PATH_PREPARED means only actual matching package imports; PATH_INCOMPLETE records
the installation/access/version/import/cap gap. Neither branch authorizes training.

Current observation uses ROOT_OPERATIONS.md and .codex/hmasd-monitor.toml:
Root01a07249-b095-7821-8ce2-e9c32ba85267 owns the shared thirty-minute fallback wake.
CM sends the actual accepted handle directly to native Root, retains observation
until adoption ACK, and retains technical collection thereafter. No retired monitor
or per-experiment automation is used. DM/root/dm_amx_cbsc_next owns intake.

## Exact command (committed before execution)

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/cbsc-system-runtime-a01-20260907/process-time.txt timeout -k 2s 598s zsh -lic 'cd /home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907 && export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 && /usr/bin/python3 scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a01_20260907/admission.json && /home/wu/.local/bin/uv venv --python /usr/bin/python3 --no-python-downloads /home/wu/.venvs/hmasd-cbsc-system312-20260907 && /home/wu/.local/bin/uv pip install --python /home/wu/.venvs/hmasd-cbsc-system312-20260907/bin/python --only-binary :all: --index-strategy unsafe-best-match --index-url https://pypi.org/simple --extra-index-url https://download.pytorch.org/whl/cu118 --verbose numpy==1.26.3 torch==2.7.0+cu118 > /home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a01_20260907/install.log 2>&1 && /home/wu/.venvs/hmasd-cbsc-system312-20260907/bin/python -c '"'"'import importlib.metadata as md
import json, platform, sys
from pathlib import Path
import numpy
import torch
torch.set_num_threads(1)
packages = []
for dist in sorted(md.distributions(), key=lambda d: d.metadata["Name"].lower()):
    packages.append({"name": dist.metadata["Name"], "version": dist.version,
                     "location": str(dist.locate_file("")),
                     "installer": dist.read_text("INSTALLER"),
                     "direct_url": dist.read_text("direct_url.json")})
result = {"object": "CBSC-SYSTEM-RUNTIME-A01", "executable": sys.executable,
          "resolved_executable": str(Path(sys.executable).resolve()),
          "base_executable": sys._base_executable, "prefix": sys.prefix,
          "base_prefix": sys.base_prefix, "version": sys.version,
          "implementation": platform.python_implementation(),
          "build": platform.python_build(), "compiler": platform.python_compiler(),
          "numpy_version": numpy.__version__, "numpy_file": numpy.__file__,
          "torch_version": torch.__version__, "torch_file": torch.__file__,
          "torch_cuda_build": torch.version.cuda, "torch_threads": torch.get_num_threads(),
          "packages": packages, "host_episodes": 0, "model_calls": 0,
          "optimizer_steps": 0, "policy_evaluations": 0}
result["pins_match"] = (sys.version_info[:2] == (3, 12) and
                        numpy.__version__ == "1.26.3" and torch.__version__ == "2.7.0+cu118")
result["outcome"] = "PATH_PREPARED" if result["pins_match"] else "PATH_INCOMPLETE"
path = Path("/home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a01_20260907/summary.json")
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2))
'"'"' > /home/wu/hmasd-worktrees/cbsc-system-runtime-a01-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a01_20260907/import.log 2>&1'
```

## Outcome

Not launched at this command-freeze commit. No environment/install/import result
is yet claimed. Ordinary Git/command preparation has created no new B04 exposure.
