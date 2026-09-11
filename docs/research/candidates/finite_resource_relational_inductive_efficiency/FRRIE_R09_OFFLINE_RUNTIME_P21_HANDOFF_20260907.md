# FRRIE R09 offline runtime amendment and P21 handoff — 2026-09-07

**The complete prospective offline command is prepared.** P21 amends the setup route to
the retained 23-wheel set and a dedicated FRRIE system312 environment. Scientific source
and the R09 comparison remain fixed. This is preparation and source review; no setup,
native build, import, probe, tape or learner ran, and no FRRIE invocation is allocated.

Authority: [P21 FRRIE scope](../../portfolio/handoffs/2026-09-07-p21-fsd-ucope-frrie-continuations.md#frrie--replace-obsolete-downloads-with-the-retained-offline-inputs)
at `d3f03ffa42c19c3a3eeba176ec10bd2e19d6ade5`. Reused the [P17 shared intake](FRRIE_P17_SHARED_CP312_RUNTIME_FACTS_INTAKE_20260907.md),
historical P15 literal and R09 card's runtime/work sections. Current AGENTS, docs guidance,
evidence-spec §§4,11.4,11.8.5–11.8.7 and engineering-scope §§4–5 apply. The Portfolio
row remains ACTIVE/HIGH; this preparation changes no lifecycle, priority or working-set rule.

## 1. Prospective assignment and exact bindings

1. **Deliverable and goal:** one offline setup-through-original-R09 chain for a later
   explicit allocation. The observed CBSC package/input facts supply the setup inputs;
   the original third-root native-return comparison remains the scientific discriminator.
2. **Owned surfaces and bindings:** own this handoff, the R09 card's prospective runtime
   paragraph, the P15 successor pointer and the preparation brief. No code path is changed.
   Future source and input bindings are fixed below; the handoff's published commit is the
   command-source revision and is distinct from scientific source `43eec21e…`.
3. **Preserved semantics:** R09 [Third root](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md#third-root-fixed-before-any-output),
   [Treatment/comparator](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md#treatment-comparator-activation-and-native-trace)
   and [Work/rule](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md#work-observable-effect-margin-and-rule).
   Root/label3, beta±0.04/±1.50, LR0.003, CPU FP32 model, original FP64 reductions,
   Torch1 and `CPP_BATCH_W32_WORKERS4_THREADS1_V1` remain unchanged. Preserve the fixed
   pdb input,128 updates, N15 primary/full N9, checkpoints0/32/64/128, uniform reference,
   MEI0.005 and ordered six-branch reading. Do not substitute the later trainer or `+cpu`.
4. **Acceptance:** current work checks the exact command, retained-input mapping and
   source boundaries only. Later CM acceptance requires actual runtime/source facts,
   fresh admissions, original learner/evaluation counts, primary and terminal evidence;
   DM applies the unchanged R09 rule. CBSC imports do not certify FRRIE's native or learner
   path. Reuse original accepted source checks; no separate import certificate or smoke.
5. **Budget and stop:** P21 authorizes preparation only. The prospective chain retains
   four attributed hours per arm and eight complete hours, with outer TERM28,795seconds
   plus at most5seconds grace. Setup, imports, native build, learning, evaluation,
   publication and termination all stay in this single cap. No retry, resume, added
   seed/arm, diagnostic or cap increase is included.

| Binding | Exact prospective value |
| --- | --- |
| Scientific and preflight source | `43eec21e9584c83e5e8d940402d7e4570b454e59` |
| Execution node / supervisor | `wsl_4070`, SSH `hmasd-wsl-node`, `/usr/local/bin/agent-task` |
| Detached worktree | `/home/wu/hmasd-worktrees/frrie-r09-system312-offline-p21-43eec21e` |
| Dedicated environment | `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907` |
| Base interpreter | `/usr/bin/python3.12`, observed CPython3.12.3 / GCC13.3.0 |
| Entry | `python -m pdb -c continue -m scripts.run_frrie_b01_contact_r09`, seed3 |
| Prospective handle | `frrie-r09-system312-offline-p21-43eec21e` |
| Output root | detached worktree's `temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_system312_offline_p21/` |
| Primary subtree | output root's `learner/`, published by the unchanged runner |
| Package input set | retained directory below; all23 exact pins appear in the literal |

The retained input directory is
`/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907/temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907/wheels/`.
Its collected23 entries are21 A03 container symlinks plus the complete cp312 Torch and
Triton files. P17's version comparison matches every P15 pin, including NumPy1.26.3,
Torch2.7.0+cu118 and Triton3.3.0. Source evidence is CBSC's P17 E0 at
`c262eda594348d62bd21d0f0c3753269157e2f1a`, already taken in at FRRIE `7581956c4`.
No fresh body read, remote inventory, dependency resolution or acquisition is needed to
prepare this command. Preserve that retained directory and its21 symlink targets for use.

Root's existing exact-SHA source provisioning must materialize the source tree and
`docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt`
from the same `43eec21e…` commit before an accepted invocation. That fixed input is528
UTF-8/LF bytes, nine lines ending in `q`, SHA256
`00631d27830cfb14b002aa0268d5ccc5d3b40a72a7a8f7d44a3c4ce295a7da65`.
Name it explicitly even when the remote sparse profile omits docs. The command reads the
materialized file directly; no in-run `git show` or lazy blob retrieval is needed. This is
ordinary committed-source provisioning, with no package setup or scientific state creation.

## 2. Exact prospective command

The existing supervisor supplies its handle directory for the GNU time output. Source,
venv, output and handle paths below have not been created by P21. Both setup and learner
admissions execute on the actual node; the learner receipt is immediately adjacent to
the original runner. CBSC's earlier receipts admit neither operation.

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/frrie-r09-system312-offline-p21-43eec21e/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 28795s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc <<'FRRIE_CHAIN'
set -euo pipefail
repo=/home/wu/hmasd-worktrees/frrie-r09-system312-offline-p21-43eec21e
out="$repo/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_system312_offline_p21"
candidate=/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907
wheelhouse=/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907/temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907/wheels
cd "$repo"
export PATH=/usr/bin:/bin:/home/wu/.local/bin:/usr/lib/wsl/lib
export UV_CACHE_DIR="$out/setup/uv-cache" TMPDIR="$out/setup/tmp"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$repo/temp/directions/finite_resource_relational_inductive_efficiency/technical/p21_setup_admission.json" && {
/usr/bin/mkdir -p "$out/setup/tmp"
/home/wu/.local/bin/uv --no-config venv --python /usr/bin/python3.12 --no-python-downloads "$candidate"
/home/wu/.local/bin/uv --no-config pip install --python "$candidate/bin/python" --no-index --find-links "$wheelhouse" --only-binary :all: filelock==3.32.5 fsspec==2026.7.0 jinja2==3.1.6 markupsafe==3.0.3 mpmath==1.3.0 networkx==3.6.1 numpy==1.26.3 nvidia-cublas-cu11==11.11.3.6 nvidia-cuda-cupti-cu11==11.8.87 nvidia-cuda-nvrtc-cu11==11.8.89 nvidia-cuda-runtime-cu11==11.8.89 nvidia-cudnn-cu11==9.1.0.70 nvidia-cufft-cu11==10.9.0.58 nvidia-curand-cu11==10.3.0.86 nvidia-cusolver-cu11==11.4.1.48 nvidia-cusparse-cu11==11.7.5.86 nvidia-nccl-cu11==2.21.5 nvidia-nvtx-cu11==11.8.86 setuptools==84.0.0 sympy==1.14.0 torch==2.7.0+cu118 triton==3.3.0 typing-extensions==4.16.0 > "$out/setup/install.log" 2>&1
"$candidate/bin/python" - "$out/setup/runtime.json" <<'PY_META'
import importlib.metadata as md
import json
import platform
import sys
from pathlib import Path
packages = ['filelock', 'fsspec', 'jinja2', 'markupsafe', 'mpmath', 'networkx', 'numpy', 'nvidia-cublas-cu11', 'nvidia-cuda-cupti-cu11', 'nvidia-cuda-nvrtc-cu11', 'nvidia-cuda-runtime-cu11', 'nvidia-cudnn-cu11', 'nvidia-cufft-cu11', 'nvidia-curand-cu11', 'nvidia-cusolver-cu11', 'nvidia-cusparse-cu11', 'nvidia-nccl-cu11', 'nvidia-nvtx-cu11', 'setuptools', 'sympy', 'torch', 'triton', 'typing-extensions']
result = {
    "source_sha": "43eec21e9584c83e5e8d940402d7e4570b454e59",
    "executable": sys.executable, "base_executable": sys._base_executable,
    "prefix": sys.prefix, "base_prefix": sys.base_prefix,
    "version": sys.version, "compiler": platform.python_compiler(),
    "installed_versions": {name: md.version(name) for name in packages},
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
PY_META
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$out/learner_admission.json" && "$candidate/bin/python" -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root "$out/learner" --admission-receipt "$out/learner_admission.json" --seed 3 < "docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt"
}
FRRIE_CHAIN
```

The offline install points directly to the complete retained wheel set; it creates no
wheel symlinks and makes no body request. `--no-python-downloads`, `--no-index` and the
23 explicit pins and binary-only installation preserve the existing offline route.
The dedicated environment and task cache leave CBSC's venv unchanged. The runtime JSON
uses stdlib distribution metadata, as in P15; actual NumPy/Torch imports and the native
build occur inside the one original R09 call. There is no separate compatibility probe.

The original native route is [P14 §3](FRRIE_P14_ORIGINAL_SOURCE_LEARNER_ROUTE_PREPARATION_20260907.md#3-exact-missing-input-and-native-build-route):
`b01/r128_smoke.py::_build_adapter` uses the existing package builder/ctypes loader and
`native/frrie_ridgegate2z_external.cpp`. The command retains the observed `/usr/bin/c++`
path, original build flags and four-worker/native32 profile through the bound source.
A fresh detached source tree avoids reusing an old built native artifact. The fixed pdb
q/EOF boundary remains; original program outcome is separate from debugger/supervisor exit.

For future delivery, read this document's sole sh fence from its **published Git blob**
as UTF-8/LF, then pass the unchanged literal as one argument to
`/usr/local/bin/agent-task run frrie-r09-system312-offline-p21-43eec21e` through
`hmasd-wsl-node`. Do not round-trip the literal through a PowerShell text pipeline.
This document's full commit returned by DM binds the command; it does not replace the
scientific/preflight source SHA above. No source staging or dispatch occurred in P21.

## 3. Complete work and preparation acceptance

Machine arithmetic from the unchanged configuration gives two arms×128 updates×64
factual episodes =16,384 episodes,256 Adam steps and196,608 factual transitions.
Training native work is2×128×4,928=1,261,568 slots;18 evaluation cells supply4,608
episodes/55,296 slots, making1,316,864 native slots total. Inputs remain8,192 training
and512 evaluation tapes, shared as originally defined. Nominal LR exposure remains7.68,
not a parameter-motion bound. No search, additional seed, smoke or evaluation is added.

Actual algorithm work remains those learner/native calls. Setup adds one dedicated
venv and one full dependency install from23 retained wheels, plus the existing metadata
publication, admissions and native build inside the complete chain. Prospective new
downloads and wheel-link operations are both zero. This preparation adds only local
source/JSON reads, configuration arithmetic and syntax parsing; all runtime exposure is zero.

The original per-arm R07 anchors are150.081252563/149.906982588seconds,903seconds at
its supervisor. CBSC's174.5612299seconds includes its acquisition/setup chain and stays
attributed to CBSC. Neither measures this FRRIE offline setup/native/learner chain; its
actual cost remains unknown. Existing per-arm14,400-second and complete28,800-second
caps are unchanged, with the outer28,795+5 bound covering all task-owned runtime work.
There is no preceding cost pilot, added setup allocation or admission inferred from old
telemetry. Later actual-node admission still requires both4GiB memory floors.

Static acceptance: the literal's 23 pins match P15 and the retained P17 summary; the
preserved R09 argument vector, source and pdb input match the original bindings. Both
outer and embedded shell syntax parse, and the one embedded Python metadata block parses
as AST. The fixed-input digest was computed from Git bytes. No payload, import, build or
fixture was executed. Exact command byte count/digest and syntax receipts are recorded
below after assembly. No new source test or runtime validation machinery is introduced.

The sole sh fence is **3,419 UTF-8 bytes, zero CR bytes**, SHA256
`f5e04fc2e3d0c0d0fb0e702914173a4e7a48d51321ef6c5ec416dc2ad8cb6b28`. Both Bash parses returned0 without diagnostics;
one Python block parsed and supervisor argument quoting round-tripped unchanged.
The retained local receipt is
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p21_offline_preparation_20260907/static_acceptance.json`.

Engineering scope§4 additions:none. The one existing optional fixed pdb observation
facility remains named by the R09 card; no new implementation or facility is added.
P21 is existing-command/document preparation, excluded from CM comparison because no
new coding assignment, implementation or scientific invocation is created.

## 4. Decision, evidence ceiling and return

**Object / preparation options:** (a) apply the retained-wheel offline setup amendment
and publish one original-source complete-chain literal; (b) leave the obsolete download
recipe as the only handoff; (c) treat CBSC's imports as authority to launch FRRIE now.
Recommend/select **(a)** under P21. **Owner-delegated decision (unattended,2026-09-03
instruction): (a).** The R09 card receives only this prospective runtime amendment;
its scientific question, work, prediction and rule are unchanged. Actual allocation is zero.

Strongest support is the retained complete input set and observed matching package
imports. Strongest limitation is that the original FRRIE native/learning chain has not
run on this stack. Earlier download failures and old uv-stack corruption remain intact,
with no causal or stability conclusion. R06–R08 signs, MEI0.005, the unscored R09
prediction and absent tuned same-information headroom record are unchanged. This ready
command is neither runtime readiness nor a positive scientific result. No owner prediction
is scored; the owner slot remains not taken.

Owner reviews at the clean boundary returned `[]`; relevant audit owner cells are empty.
No new card, P1/P2 item, direction-tier change or Portfolio disposition is made. A short
[Chinese preparation brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_P21-offline-route-preparation.md)
keeps the zero-execution boundary explicit. No section5 budget breach occurred.

**Ready allocation need:** Portfolio can supply one complete original-source R09 root3
pair on the amended offline route, under the original caps, with Root staging/dispatch/
observation, CM collection/technical acceptance and DM scientific intake. The runtime
choice and exact command are prepared; no additional package-discovery or import task is
needed. No unresolved input fact blocks this preparation. A later release must be explicit
because P21 supplies zero invocations; Root is not asked to select the scientific task.

Authoring reuses clean `codex/frrie` at `7581956c477be754d50e03240652a49f564178b6`,
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`. Scientific source, DIRECTION,
shared audit and other writers' paths are unchanged. Root appends this supplied row at
integration; it is not claimed already appended here:

```text
| 2026-09-07T20:54:36-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) prospective retained23-wheel offline R09 chain; (b) leave obsolete downloads; (c) launch from shared import success | (a):runtime setup amended and exact original43eec21e/root3 chain prepared; original caps/science retained; zero actual setup or invocation allocation | yes | OWNER_DELEGATED (unattended,2026-09-03instruction); P21-FRRIE | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_OFFLINE_RUNTIME_P21_HANDOFF_20260907.md | none | |
```

scope: none
