# CBSC post-A03 acquisition: exact Root handoff

**Ready for separate execution release; P10 preparation only.** The existing
selected literal is extractable and passes focused local Bash syntax checking.
No network request, source staging, admission or candidate invocation occurred.
Source review establishes delivery readiness, not installed-candidate readiness.

## Contract and distinct source bindings

Card: [Frozen input and command bindings / Work, exposure, execution and stop](CBSC_POST_A03_ACQUISITION_SCIENCE_CARD_20260907.md).
Selection: [Bounded CM handoff and acceptance](CBSC_POST_A03_ACQUISITION_SELECTION_20260907.md).
Shared checkout `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch
`codex/cbsc`, began tracked-clean at `0c09af0de`. Only this handoff changes;
DM's editing/index window resumes after this commit/push return.

- **Command source:** `71131d728a0b5f04663301e3d838e699ce70af41`,
  `docs/research/candidates/capability_bound_semantic_currentness/CBSC_POST_A03_ACQUISITION_PATH_ADDENDUM_20260907.md`,
  sole sh fence under Exact prospective command. Use those committed bytes,
  not the current checkout's potentially CRLF-normalized document.
- **Preflight source:** `ec8866b3968fcb1566976ce405d7c552d4d9a5de`,
  `scripts/hmasd_resource_preflight.py`. This is the detached worktree revision
  and the JSON `preflight_source_sha` value. It is not the command-source revision.
- Any future accepted-handle/collection record must retain both bindings above.
  The literal metadata JSON is unchanged; no field, validator or currentness guard
  is added to it. The card and this handoff preserve the command identity separately.

Node wsl_4070 / SSH hmasd-wsl-node. Existing supervisor `/usr/local/bin/agent-task`.
Handle `cbsc-post-a03-acquisition-proposal-20260907`.
Detached preflight worktree:
`/home/wu/hmasd-worktrees/cbsc-post-a03-acquisition-proposal-20260907`.
Output:
`/home/wu/hmasd-worktrees/cbsc-post-a03-acquisition-proposal-20260907/temp/directions/capability_bound_semantic_currentness/exp/post_a03_acquisition_proposal_20260907`.
Candidate `/home/wu/.venvs/hmasd-cbsc-system312-post-a03-proposal-20260907`.
No local fallback. The fixed remote source worktree and supervisor directory must
be made available through the existing route only after an explicit release;
this preparation did not stage them. Supervisor creates its own log directory.

## Literal command artifact

The following sh fence is the exact UTF-8/LF command extracted from the bound
commit: **7226 bytes, zero CR bytes**, without its surrounding fence or
trailing fence newline. It is copied verbatim, not rebuilt or requoted internally.

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/.agent-tasks/cbsc-post-a03-acquisition-proposal-20260907/process-time.txt /usr/bin/timeout --signal=KILL 540s /usr/bin/env -u BASH_ENV -u ENV -u ALL_PROXY -u all_proxy /bin/bash --noprofile --norc -c 'set -euo pipefail
repo=/home/wu/hmasd-worktrees/cbsc-post-a03-acquisition-proposal-20260907
out=/home/wu/hmasd-worktrees/cbsc-post-a03-acquisition-proposal-20260907/temp/directions/capability_bound_semantic_currentness/exp/post_a03_acquisition_proposal_20260907
candidate=/home/wu/.venvs/hmasd-cbsc-system312-post-a03-proposal-20260907
cd "$repo"
export UV_CACHE_DIR="$out/uv-cache" TMPDIR="$out/tmp"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export no_proxy='"'"'localhost,127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8'"'"' NO_PROXY='"'"'localhost,127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8'"'"'
/usr/bin/python3 scripts/hmasd_resource_preflight.py admit-memory --out "$out/admission.json" && {
/usr/bin/mkdir -p "$out/wheels" "$out/tmp"
/home/wu/.local/bin/uv --no-config venv --python /usr/bin/python3 --no-python-downloads "$candidate"
/usr/bin/python3 - "$out/wheels" <<'"'"'PY_LINK'"'"'
from pathlib import Path
import sys
source = Path('"'"'/home/wu/hmasd-worktrees/cbsc-system-runtime-a03-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a03_20260907/wheels'"'"')
target = Path(sys.argv[1])
for name in ['"'"'filelock-3.32.5-py3-none-any.whl'"'"', '"'"'fsspec-2026.7.0-py3-none-any.whl'"'"', '"'"'jinja2-3.1.6-py3-none-any.whl'"'"', '"'"'markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl'"'"', '"'"'mpmath-1.3.0-py3-none-any.whl'"'"', '"'"'networkx-3.6.1-py3-none-any.whl'"'"', '"'"'numpy-1.26.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cublas_cu11-11.11.3.6-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cuda_cupti_cu11-11.8.87-py3-none-manylinux1_x86_64.whl'"'"', '"'"'nvidia_cuda_nvrtc_cu11-11.8.89-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cuda_runtime_cu11-11.8.89-py3-none-manylinux1_x86_64.whl'"'"', '"'"'nvidia_cudnn_cu11-9.1.0.70-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cufft_cu11-10.9.0.58-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_curand_cu11-10.3.0.86-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cusolver_cu11-11.4.1.48-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_cusparse_cu11-11.7.5.86-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_nccl_cu11-2.21.5-py3-none-manylinux2014_x86_64.whl'"'"', '"'"'nvidia_nvtx_cu11-11.8.86-py3-none-manylinux1_x86_64.whl'"'"', '"'"'setuptools-84.0.0-py3-none-any.whl'"'"', '"'"'sympy-1.14.0-py3-none-any.whl'"'"', '"'"'typing_extensions-4.16.0-py3-none-any.whl'"'"']:
    (target / name).symlink_to(source / name)

PY_LINK
/usr/bin/curl -q --fail --location --retry 0 --output "$out/wheels/torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl" https://download.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl
/usr/bin/curl -q --fail --location --retry 0 --output "$out/wheels/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl" https://download.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
/home/wu/.local/bin/uv --no-config pip install --python "$candidate/bin/python" --no-index --find-links "$out/wheels" --only-binary :all: filelock==3.32.5 fsspec==2026.7.0 jinja2==3.1.6 markupsafe==3.0.3 mpmath==1.3.0 networkx==3.6.1 numpy==1.26.3 nvidia-cublas-cu11==11.11.3.6 nvidia-cuda-cupti-cu11==11.8.87 nvidia-cuda-nvrtc-cu11==11.8.89 nvidia-cuda-runtime-cu11==11.8.89 nvidia-cudnn-cu11==9.1.0.70 nvidia-cufft-cu11==10.9.0.58 nvidia-curand-cu11==10.3.0.86 nvidia-cusolver-cu11==11.4.1.48 nvidia-cusparse-cu11==11.7.5.86 nvidia-nccl-cu11==2.21.5 nvidia-nvtx-cu11==11.8.86 setuptools==84.0.0 sympy==1.14.0 torch==2.7.0+cu118 triton==3.3.0 typing-extensions==4.16.0 > "$out/install.log" 2>&1
"$candidate/bin/python" - "$out" ec8866b3968fcb1566976ce405d7c552d4d9a5de "$candidate/bin/python" <<'"'"'PY_META'"'"'
import importlib.metadata as md
import json, platform, sys
from pathlib import Path
import numpy
import torch
expected = {'"'"'filelock'"'"': '"'"'3.32.5'"'"',
 '"'"'fsspec'"'"': '"'"'2026.7.0'"'"',
 '"'"'jinja2'"'"': '"'"'3.1.6'"'"',
 '"'"'markupsafe'"'"': '"'"'3.0.3'"'"',
 '"'"'mpmath'"'"': '"'"'1.3.0'"'"',
 '"'"'networkx'"'"': '"'"'3.6.1'"'"',
 '"'"'numpy'"'"': '"'"'1.26.3'"'"',
 '"'"'nvidia-cublas-cu11'"'"': '"'"'11.11.3.6'"'"',
 '"'"'nvidia-cuda-cupti-cu11'"'"': '"'"'11.8.87'"'"',
 '"'"'nvidia-cuda-nvrtc-cu11'"'"': '"'"'11.8.89'"'"',
 '"'"'nvidia-cuda-runtime-cu11'"'"': '"'"'11.8.89'"'"',
 '"'"'nvidia-cudnn-cu11'"'"': '"'"'9.1.0.70'"'"',
 '"'"'nvidia-cufft-cu11'"'"': '"'"'10.9.0.58'"'"',
 '"'"'nvidia-curand-cu11'"'"': '"'"'10.3.0.86'"'"',
 '"'"'nvidia-cusolver-cu11'"'"': '"'"'11.4.1.48'"'"',
 '"'"'nvidia-cusparse-cu11'"'"': '"'"'11.7.5.86'"'"',
 '"'"'nvidia-nccl-cu11'"'"': '"'"'2.21.5'"'"',
 '"'"'nvidia-nvtx-cu11'"'"': '"'"'11.8.86'"'"',
 '"'"'setuptools'"'"': '"'"'84.0.0'"'"',
 '"'"'sympy'"'"': '"'"'1.14.0'"'"',
 '"'"'torch'"'"': '"'"'2.7.0+cu118'"'"',
 '"'"'triton'"'"': '"'"'3.3.0'"'"',
 '"'"'typing-extensions'"'"': '"'"'4.16.0'"'"'}
versions = {name: md.version(name) for name in expected}
result = {
    "object": "CBSC-POST-A03-ACQUISITION-PROPOSAL", "preflight_source_sha": sys.argv[2],
    "executable": sys.executable, "resolved_executable": str(Path(sys.executable).resolve()),
    "base_executable": sys._base_executable, "prefix": sys.prefix,
    "base_prefix": sys.base_prefix, "version": sys.version,
    "implementation": platform.python_implementation(),
    "build": platform.python_build(), "compiler": platform.python_compiler(),
    "numpy_version": numpy.__version__, "numpy_file": numpy.__file__,
    "torch_version": torch.__version__, "torch_file": torch.__file__,
    "torch_cuda_build": torch.version.cuda, "installed_versions": versions,
    "distributions": [{"name": d.metadata["Name"], "version": d.version,
                       "location": str(d.locate_file("")), "installer": d.read_text("INSTALLER"),
                       "direct_url": d.read_text("direct_url.json")}
                      for d in sorted(md.distributions(), key=lambda d: d.metadata["Name"].lower())],
    "host_episodes": 0, "model_calls": 0, "optimizer_steps": 0, "policy_evaluations": 0,
}
result["metadata_matches"] = (
    sys.version_info[:3] == (3, 12, 3) and versions == expected
    and numpy.__version__ == "1.26.3" and torch.__version__ == "2.7.0+cu118"
    and torch.version.cuda == "11.8" and sys.executable == sys.argv[3]
    and Path(numpy.__file__).is_relative_to(sys.prefix)
    and Path(torch.__file__).is_relative_to(sys.prefix))
path = Path(sys.argv[1]) / "summary.json"
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2))
sys.exit(0 if result["metadata_matches"] else 1)
PY_META
}
'
```

## LF-safe extraction and direct delivery

The ready extraction/delivery recipe below reads the committed blob as bytes,
extracts only its sole sh fence, then passes one quoted command argument to the
existing supervisor. It performs no shell expansion on the Windows control plane.
`shlex.join` quotes the remote supervisor argv; it does not alter the inner literal.
Do not round-trip command bytes through PowerShell text pipelines or write them
through newline-translating text streams. The previous A03 syntax-check transport
conversion is avoided by this byte-preserving extraction. No login shell is added.

The final subprocess line is **for a future explicit execution release only**;
it was not run in this preparation. Source staging remains a distinct existing
Root task, with detached preflight SHA above, not an extra result invocation.

```python
import shlex
import subprocess

source = "71131d728a0b5f04663301e3d838e699ce70af41"
path = "docs/research/candidates/capability_bound_semantic_currentness/CBSC_POST_A03_ACQUISITION_PATH_ADDENDUM_20260907.md"
blob = subprocess.check_output(["git", "show", source + ":" + path])
command = blob.split(b"```sh\n", 1)[1].split(b"\n```", 1)[0].decode("utf-8")
remote_argv = shlex.join([
    "/usr/local/bin/agent-task", "run",
    "cbsc-post-a03-acquisition-proposal-20260907", command,
])
subprocess.run(["ssh", "hmasd-wsl-node", remote_argv], check=True)
```

On a later accepted send, follow that exact handle to terminal evidence or Root
adoption; uncertain acceptance means query the same handle, never send again
blindly. Retain supervisor start/end, process-time, admission and primary/error
artifacts. Root observes within the owner's active goal, CM collects technically,
DM intakes. No new scheduler or heartbeat is created.

## Static acceptance and preserved work

Local `C:/Program Files/Git/bin/bash.exe --noprofile --norc -n` consumed the exact
command bytes on stdin with BASH_ENV/ENV removed: exit0, no diagnostic. Bash did
not execute the command. Remote-argv quoting round-trip returned the identical
UTF-8 literal. Earlier embedded Python parsing is reused; no duplicate Python
runtime check, candidate smoke or metadata request was performed. The copied
handoff fence was compared to the bound source fence and is identical.

Preserved literal work:21named retained-container symlinks, both complete cp312
body requests (1,111,959,613bytes), all23pins, one offline binary full-dependency
install and one metadata process/JSON readback. Old21containers and partial Torch
stay untouched; the partial body is excluded and receives no transfer credit.
The fixed localhost proxy and canonical endpoints remain as selected, without
new configuration, retry/resume/range requests or speculative transport changes.

Outer GNU time precedes all task-owned shell/environment setup. Existing timeout
KILL540 covers admission, candidate/links, both sequential downloads, install,
imports, publication and termination inside the proposed600s complete cap. Fresh
actual-node memory preflight is joined directly with && to candidate work; both
4GiB floors apply. Actual complete wall and metadata, not flags or source review,
control the frozen PATH_PREPARED/PATH_INCOMPLETE reading. Earlier partial-transfer
failures and unknown body/install/import time remain relevant uncertainties.

Engineering-scope section4 additions:none. No new runner/source change, schema,
validator, source-currentness check, standalone test or runtime call. Current
preparation exposure:zero network/HEAD/body reads, admission, venv creation,
installation, candidate import, throughput probe or scientific calls. No concrete
command-delivery gap was found. Execution allocation remains zero until separately
released. Return the ready handoff to DM/Root; this push is not that release.
