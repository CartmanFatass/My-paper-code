# FRRIE P15 cp312 Torch metadata intake and prospective setup

Later evidence: [CBSC P17 shared-runtime intake](FRRIE_P17_SHARED_CP312_RUNTIME_FACTS_INTAKE_20260907.md)
resolves the missing complete-body input and records matching package imports. This P15
record and its baseline command remain historical; FRRIE execution remains unallocated.
P21's [offline successor](FRRIE_R09_OFFLINE_RUNTIME_P21_HANDOFF_20260907.md) supplies the
prospectively amended command from those retained inputs. The P15 literal below is unchanged.

**The P14 artifact-identification gap is resolved.** Select system CPython3.12.3 with
NumPy1.26.3 and Torch2.7.0+cu118 as the prospective runtime for original R09 source
`43eec21e9584c83e5e8d940402d7e4570b454e59`. This is an object-tier preparation decision,
not an applied card amendment or execution release. Complete wheel bodies and the
setup/native/learner path remain unavailable or unobserved. No scientific result is added.

## 1. Assignment, reading rule and direct evidence

The [P15 FRRIE assignment](../../portfolio/handoffs/2026-09-07-p15-rolling-refill-after-transport-split.md#frrie--resolve-the-actual-cp312-artifact-input)
at `25b1a88b162ae137b5071ca2d9acb87007fb3ea9` supplied the metadata question before
observation. Reused [P14 §§2–4](FRRIE_P14_ORIGINAL_SOURCE_LEARNER_ROUTE_PREPARATION_20260907.md#2-direct-installed-metadata-and-its-limits),
the R09 card's work/portability/debugger sections, A03/A04 stop boundaries and the
shared [CBSC exact handoff](../capability_bound_semantic_currentness/CBSC_POST_A03_ACQUISITION_ROOT_HANDOFF_20260907.md)
and [failed-acquisition intake](../capability_bound_semantic_currentness/CBSC_POST_A03_ACQUISITION_INTAKE_20260907.md).
Applied AGENTS focused reading, evidence-spec §§4,5.1,11.4,11.8.5–11.8.7 and11.9,
and engineering-scope §§4–5. No new mechanism, comparator or literature claim was selected.

The controlling P15 scope, applied verbatim:

> at most six metadata requests, each bounded to 30 s and 2 MiB; no wheel-body acquisition, install, import, build, probe, tape or learner. No experiment budget is added.

The [sourced metadata record](FRRIE_P15_CP312_TORCH_METADATA_20260907.json) contains
all five request receipts, selected official index anchors, exact package requirements,
published artifact hashes and the reused21-container/23-pin setup inventory. Raw response
bodies remain under `temp/directions/finite_resource_relational_inductive_efficiency/exp/p15_torch_metadata_20260907/`.
Only public content/date/ETag headers are copied into the durable record.

| Request | Official response | Bytes | Wall seconds |
| --- | --- | ---: | ---: |
| 1 | cu118 Torch package index | 77,378 | 1.6981749 |
| 2 | advertised R2 cp312 Torch `.whl.metadata` | 28,944 | 1.4813097 |
| 3 | canonical cp312 Torch `.whl.metadata` | 28,944 | 1.5102693 |
| 4 | Triton package index | 82,279 | 2.1052376 |
| 5 | canonical cp312 Triton `.whl.metadata` | 1,533 | 1.4458790 |

All returned200 without redirects or retries. Offline stdlib analysis counted
**5/6 requests,219,078 response bytes and8.2408705 summed request seconds**; the latter
is not task elapsed time or full-wheel cost. Each request enforced a30-second cancellation
and2,097,152-byte response cap. No sixth request was needed. Wheel-body requests/bytes,
admissions, installs, package imports, builds, probes, tapes, learner/optimizer steps and
evaluations were all zero. Resource telemetry beyond request time/bytes is
`resources_unmeasured`; there is no result-bearing invocation or section5 budget breach.

## 2. Artifact resolution and bounded interpretation

The [official cu118 index](https://download.pytorch.org/whl/cu118/torch/) advertises
`torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl`. Its actual wheel tags are
CPython312 / cp312 ABI / Linux x86_64 manylinux2.28. The corresponding
[canonical metadata](https://download.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl.metadata)
declares Torch2.7.0+cu118 and Python>=3.9.0. R2 and canonical metadata bytes have the
same SHA256, matching the official index's metadata digest:

```text
Torch metadata: 96c80f6b26b1d671227587977b032d76e52012a68b623974432032725338e2c5
Torch wheel, index-advertised only: f536e66abf9a989e66a19ef460f54f6014db54cbdbb04c6daf7ddf0b8f3151c4
```

For Python3.12/Linux x86_64, its CUDA/cuDNN/NCCL and Triton requirements still apply
to this distribution when FRRIE uses CPU tensors. The shared23 pins satisfy the visible
Torch requirements, including `setuptools`, `typing-extensions>=4.10.0` and
`sympy>=1.13.3`. Torch requires Triton3.3.0 on this platform. The
[official Triton index](https://download.pytorch.org/whl/triton/) supplies
`triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl`.
Its [metadata](https://download.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata)
has no Requires-Python field and requires `setuptools>=40.8.0` without extras.
Selected extras are empty for both packages. The Triton metadata also matches its
published metadata digest:

```text
Triton metadata: 8b86c432af86b40b12200ed9456fd8350503114260abb6a45e9b0c1216cbd2d1
Triton wheel, index-advertised only: 0f12a8611eff721d3fd837d0cc2a1f2f8a4d382ec3fc3a8d6a07a5b1e535c81c
```

This establishes the exact artifact/ABI/dependency input missing from P14. It does
not establish full wheel identity from received body bytes, current retained-container
availability, successful transfer/install/import, native ABI behavior or R09 readiness.
The other21 containers/versions are reused CBSC evidence, not a new transitive-index
resolution. No package wheel was opened or read in this task.

The strongest support is matching official index/metadata plus A04's existing bounded
system312/NumPy success. The strongest contrary observation is CBSC's complete-body
failure on the canonical Torch endpoint:444,302/955,455,844bytes, curl18,2.85seconds;
its earlier R2 attempt also left a partial body. Small metadata200 responses are not
evidence that either full-body path was repaired, nor a proxy/endpoint causal diagnosis.
The R09 learner and native build remain unobserved on the candidate stack. A03's old
uv-stack corruption and all earlier quarantine remain unchanged.

## 3. Explicit runtime selection and complete prospective command

Select the P14 minimally changed candidate: `/usr/bin/python3.12` (observed CPython3.12.3),
the exact NumPy/Torch versions above and CBSC's23 dependency pins in a separate FRRIE
venv. Bind the entire original R09 commit, not current HEAD or A04's later imported
trainer. Preserve CPU FP32 model, original FP64 reductions, Torch1,
`CPP_BATCH_W32_WORKERS4_THREADS1_V1`, original seed/root/label3, LR0.003,
beta±0.04/±1.50,128updates, N15 primary/full N9, checkpoints0/32/64/128,
uniform reference, MEI0.005 and the ordered six-branch rule.

The literal below is a **prospective baseline recipe only**, including setup through
the original single R09 invocation so setup is charged to its complete chain. It is not
a released acquisition repair or a request to repeat the failed CBSC command. Its two
canonical full-body requests are named from verified metadata and existing CBSC source;
no supported changed acquisition condition is inferred. The exact remaining unavailable
inputs are the complete Torch and Triton bodies, historically955,455,844 and156,503,769
bytes respectively, or a separately supplied supported acquisition change. Shared CBSC
P15 work can supply that condition through Root; this task neither invents nor executes it.

Before a later release, Root supplies a fresh detached worktree at
`43eec21e9584c83e5e8d940402d7e4570b454e59` at the literal path below using the existing
configured exact-SHA route. The source tree must contain the script/package surfaces;
the retained pdb input is extracted from that same commit even with sparse checkout.
The existing supervisor creates `/home/wu/.agent-tasks/frrie-r09-system312-p15-43eec21e/`.
No worktree, input copy, venv or supervisor handle was created by this preparation.

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/frrie-r09-system312-p15-43eec21e/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 28795s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc <<'FRRIE_CHAIN'
set -euo pipefail
repo=/home/wu/hmasd-worktrees/frrie-r09-system312-p15-43eec21e
out="$repo/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_system312_p15"
candidate=/home/wu/.venvs/hmasd-frrie-system312-r09-p15-20260907
cd "$repo"
export PATH=/usr/bin:/bin:/home/wu/.local/bin:/usr/lib/wsl/lib
export UV_CACHE_DIR="$out/setup/uv-cache" TMPDIR="$out/setup/tmp"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export no_proxy='localhost,127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8'
export NO_PROXY="$no_proxy"
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$repo/temp/directions/finite_resource_relational_inductive_efficiency/technical/p15_setup_admission.json" && {
/usr/bin/mkdir -p "$out/setup/wheels" "$out/setup/tmp"
/home/wu/.local/bin/uv --no-config venv --python /usr/bin/python3.12 --no-python-downloads "$candidate"
/usr/bin/python3.12 - "$out/setup/wheels" <<'PY_LINK'
from pathlib import Path
import sys
source = Path('/home/wu/hmasd-worktrees/cbsc-system-runtime-a03-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a03_20260907/wheels')
target = Path(sys.argv[1])
for name in [
    'filelock-3.32.5-py3-none-any.whl',
    'fsspec-2026.7.0-py3-none-any.whl',
    'jinja2-3.1.6-py3-none-any.whl',
    'markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl',
    'mpmath-1.3.0-py3-none-any.whl',
    'networkx-3.6.1-py3-none-any.whl',
    'numpy-1.26.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl',
    'nvidia_cublas_cu11-11.11.3.6-py3-none-manylinux2014_x86_64.whl',
    'nvidia_cuda_cupti_cu11-11.8.87-py3-none-manylinux1_x86_64.whl',
    'nvidia_cuda_nvrtc_cu11-11.8.89-py3-none-manylinux2014_x86_64.whl',
    'nvidia_cuda_runtime_cu11-11.8.89-py3-none-manylinux1_x86_64.whl',
    'nvidia_cudnn_cu11-9.1.0.70-py3-none-manylinux2014_x86_64.whl',
    'nvidia_cufft_cu11-10.9.0.58-py3-none-manylinux2014_x86_64.whl',
    'nvidia_curand_cu11-10.3.0.86-py3-none-manylinux2014_x86_64.whl',
    'nvidia_cusolver_cu11-11.4.1.48-py3-none-manylinux2014_x86_64.whl',
    'nvidia_cusparse_cu11-11.7.5.86-py3-none-manylinux2014_x86_64.whl',
    'nvidia_nccl_cu11-2.21.5-py3-none-manylinux2014_x86_64.whl',
    'nvidia_nvtx_cu11-11.8.86-py3-none-manylinux1_x86_64.whl',
    'setuptools-84.0.0-py3-none-any.whl',
    'sympy-1.14.0-py3-none-any.whl',
    'typing_extensions-4.16.0-py3-none-any.whl'
]:
    (target / name).symlink_to(source / name)
PY_LINK
/usr/bin/curl -q --fail --location --retry 0 --output "$out/setup/wheels/torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl" https://download.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl
/usr/bin/curl -q --fail --location --retry 0 --output "$out/setup/wheels/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl" https://download.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
/home/wu/.local/bin/uv --no-config pip install --python "$candidate/bin/python" --no-index --find-links "$out/setup/wheels" --only-binary :all: filelock==3.32.5 fsspec==2026.7.0 jinja2==3.1.6 markupsafe==3.0.3 mpmath==1.3.0 networkx==3.6.1 numpy==1.26.3 nvidia-cublas-cu11==11.11.3.6 nvidia-cuda-cupti-cu11==11.8.87 nvidia-cuda-nvrtc-cu11==11.8.89 nvidia-cuda-runtime-cu11==11.8.89 nvidia-cudnn-cu11==9.1.0.70 nvidia-cufft-cu11==10.9.0.58 nvidia-curand-cu11==10.3.0.86 nvidia-cusolver-cu11==11.4.1.48 nvidia-cusparse-cu11==11.7.5.86 nvidia-nccl-cu11==2.21.5 nvidia-nvtx-cu11==11.8.86 setuptools==84.0.0 sympy==1.14.0 torch==2.7.0+cu118 triton==3.3.0 typing-extensions==4.16.0 > "$out/setup/install.log" 2>&1
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
/usr/bin/git show 43eec21e9584c83e5e8d940402d7e4570b454e59:docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt > "$out/setup/pdb_stdin.txt"
/usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out "$out/learner_admission.json" && "$candidate/bin/python" -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 --output-root "$out/learner" --admission-receipt "$out/learner_admission.json" --seed 3 < "$out/setup/pdb_stdin.txt"
}
FRRIE_CHAIN
```

The ordinary source-defined native build is reached inside that one R09 call;
P14 §3 supplies its original C++ entry and flags. The metadata process above uses
stdlib distribution metadata only and is part of setup, not a package-import smoke or
a second scientific observation. Actual imports/builds occur in the original runner.
The fixed pdb input retains q/EOF termination and does not authorize a restart.
Original program outcome, learner summary and debugger/supervisor exit remain distinct.

Task inputs and outputs use distinct paths. Only the21 explicitly named complete
containers are linked from CBSC; old partial Torch files are excluded and preserved.
There is no dependency re-resolution, package substitution, shared-venv mutation,
download retry/resume/range request, source change, new guard or new validator.

For eventual delivery, extract the sole sh fence from this document's **committed blob**
as UTF-8/LF bytes; do not round-trip it through a PowerShell text pipeline. Pass it as one
quoted command argument to existing `/usr/local/bin/agent-task run
frrie-r09-system312-p15-43eec21e` via configured `hmasd-wsl-node`. Source staging and
dispatch are future Root work after the separately named allocation. A changed acquisition
condition requires an updated exact literal before execution, retaining the source,
package pins, science and complete cap; this baseline is not silently modified at launch.

## 4. Cost, acceptance and later allocation

The proposed complete chain has one setup,21retained links, two full-body requests
totaling1,111,959,613expected bytes,23exact pins and one R09 seed3 pair. Original
learning work is two arms×128updates×64factual episodes,256Adam steps,
196,608factual transitions and1,261,568training native slots;18evaluation cells,
4,608evaluation episodes and55,296evaluation slots make1,316,864native slots total.
Inputs are8,192training+512evaluation tapes. Nominal exposure7.68 is not a motion bound.
These are reused P13 machine calculations, not newly executed work. Added diagnostic,
smoke, training-seed, comparator and search invocations are zero.

R07's150.081252563/149.906982588attributed seconds per arm and903supervisor seconds
are historical planning anchors; A04's16seconds is only its T0 path. Neither prices the
new complete setup/native/learning chain. Body/install/import cost and reliable transfer
are unknown. Keep the existing four attributed hours per arm/eight total hours; outer
TERM28,795seconds plus at most5seconds grace covers all task-owned setup, admission,
imports/build, training, evaluation, publication and termination. No separate setup
allocation, profiling task or longer cap is introduced. Existing setup and learner
admissions each precede their work; the latter is immediately adjacent to the original
runner and measures both >=4GiB floors. Actual execution admission remains future work.

The later complete return must contain actual runtime/dependency metadata, bound source
and root/LR, admissions, terminal/primary artifacts, original learner/evaluation counts,
all outcomes and whole-chain wall. CM owns direct collection/technical acceptance;
DM applies the original R09 rule. No import certificate, exact-output comparison,
causal panel or repeated smoke is made an additional B prerequisite. If code compatibility
fails, return its exact defect; a genuinely new CM implementation assignment goes through
Root's applicable five-arm capture before coding. This metadata/command preparation is
excluded because it creates no coding assignment, source implementation or scientific call.

Local acceptance: parsed each retained response/receipt and computed hashes/counts with
stdlib tools; checked the shared21 filenames and23 pins against CBSC's committed exact
command. The prospective outer command and embedded shell passed Bash syntax-only
parsing; embedded Python blocks passed AST parsing. No command was executed. Engineering
scope§4 additions:none; the command only reuses the R09 card's existing fixed pdb facility
and configured supervisor. No mechanism-level conclusion is added to DIRECTION.md.
The sole sh fence is5,702UTF-8 bytes with zero CR bytes, SHA256
`180075192d8e36d844001d5067009e27ad65f0b69b1a3da8e8d1cf48a544a201`.
The local syntax receipt is retained beside the raw requests as `static_acceptance.json`;
both Bash parses returned0 without diagnostics and both Python blocks parsed.

## 5. Decisions this intake produces

1. **Object / technical:** (a) accept exact artifact/metadata resolution at A/RECON;
   (b) treat metadata200 as full-wheel or learner readiness; (c) infer an old corruption
   cause or algorithm sign. Recommend/select **(a)**. The direct bytes support only
   package identity/requirements and bounded endpoint response, not the stronger claims.
2. **Object / preparation selection:** (a) select the original-source system312/cu118
   candidate and return the complete baseline recipe plus unavailable complete-body/
   acquisition input; (b) substitute `+cpu`, later trainer or different worker profile;
   (c) run setup/learner from the unused metadata allowance. Recommend/select **(a)**.
   This is the explicit prospective runtime decision requested by P15. No card freeze,
   applied runtime amendment, acquisition repair, additional invocation or R09 release follows.

**Owner-delegated decision (unattended,2026-09-03instruction): (a) for each decision.**
The source/version constraints also follow P15 directly. Both are reversible object
decisions; no direction-tier recast, family change, UAV entry, lifecycle or investment
action is selected. Owner flags:none. No new P1/P2 item is needed for these ordinary
technical/preparation decisions. At the clean boundary, owner reviews returned `[]`;
FRRIE audit owner cells remain empty. Owner prediction is not taken; no new performance
prediction was made or scored, and the R09 prediction remains awaiting a valid learner result.

The metadata question has no native-return MEI or host-headroom observation; the direction
still has no tuned same-information host-headroom record. Existing
science remains bounded: R06 first-root N15+.005548293532 supports a conditional signal,
R07 second-root−.001948094523 contradicts recurrence at MEI.005, and R08's+.000010174094
chart-cut attenuation is same-root evidence. None is revised by package availability.
The next scientific discriminator remains the complete third-root comparison.

**Next owner:** Root integrates this record and shares the exact artifact evidence with
CBSC, then returns the missing complete bodies/supported acquisition condition and the
prospective runtime choice to Portfolio for a concrete later allocation. Recommend one
original-source setup-through-R09 chain after that acquisition input is selected, under
the original caps and with no retry; do not add another tape/causal diagnostic. P15 ends
here with zero setup/learner allocation. Root is not asked to choose the scientific task.

Authoring reused clean `codex/frrie` at `f7e37cdb3e18778bcc533d6b300c08a116f65d08` in
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`. Own only this handoff, the
metadata JSON and [Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_P15-cp312-torch-metadata.md).
No shared audit, card, source, DIRECTION or unrelated work was edited. Root appends these
exact rows at integration; they are not claimed already appended:

```text
| 2026-09-07T17:35:19-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept exact cp312 Torch/Triton metadata; (b) infer full-body/learner readiness; (c) infer corruption cause or algorithm sign | (a):5/6 bounded official metadata requests,219078bytes; hashes and requirements resolved; zero wheel bodies/setup/learner | yes | OWNER_DELEGATED (unattended,2026-09-03instruction); P15-FRRIE | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_P15_CP312_TORCH_SETUP_HANDOFF_20260907.md | none | |
| 2026-09-07T17:35:19-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) prospective original43eec21e/system312/cu118 runtime plus exact remaining acquisition input; (b) substitute variant/trainer/workers; (c) execute outside P15 | (a):complete prospective baseline recipe, no amendment or release; complete Torch/Triton bodies or supported changed acquisition condition remain unavailable | yes | OWNER_DELEGATED (unattended,2026-09-03instruction); P15-FRRIE | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_P15_CP312_TORCH_SETUP_HANDOFF_20260907.md | none | |
```

scope: none
