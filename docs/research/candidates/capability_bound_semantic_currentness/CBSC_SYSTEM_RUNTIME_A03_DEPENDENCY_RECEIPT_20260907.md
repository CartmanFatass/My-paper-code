# CBSC A03 dependency-path inspection receipt

**Return: exact acquisition/cost gap; no fresh invocation prepared or selected.**
The unchanged-binary route is existing compatible uv cache plus eight official
wheel acquisitions. Those missing bodies total **2,111,900,299 bytes**
(2014.065 MiB). HEAD availability exists for all eight, but neither sustained
transfer throughput nor complete install/import/publication cost is established.
A credible complete <=600s projection cannot be supplied from these facts.
This is an unmeasured cost gap, not proof that completion inside 600s is impossible.

## Scope and actual starting state

Assignment: [P08 handoff](CBSC_P08_DEPENDENCY_PATH_HANDOFF_20260907.md), Five-item
CM handoff. Inputs: A02 intake Observation / Return, E0 and the prior CM record.
Shared checkout `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch
`codex/cbsc`, began tracked-clean at `70ed2f1ae43a5406ed99eb59be5692dff2b12716`.
DM transferred the editing/index window; only this receipt is tracked by CM.
No new authoring checkout or branch. Engineering-scope section 4 additions: none.

Read-only node: `wsl_4070` via `hmasd-wsl-node`, stdlib `/usr/bin/python3` control
scripts; no candidate library imports. The retained environment is
`/home/wu/.venvs/hmasd-cbsc-system312-a02-20260907`. Its pyvenv.cfg reports
CPython 3.12.3, home `/usr/bin`, uv 0.12.9, system-site-packages false.
Its site-packages contains only `_virtualenv.py` and `_virtualenv.pth`.
No NumPy, Torch or required dependency is installed there.

Scoped cache inspection used `/home/wu/.cache/uv/wheels-v6/pypi` and its two
existing index buckets `0683d010c15737d1` / `fc5d3190421f7703`, only the 23 package
names selected by the retained A02 log. Only their symlink-target archives were
opened under `/home/wu/.cache/uv/archive-v0`; there was no whole-cache census.
The retained A02 log reports 23 resolved packages in 5.40s; that is old resolver
cost only and provides no successful complete-path or transfer-rate estimate.

## Archive candidates: structural completeness, not integrity certification

For matching version/tag archive candidates, inspection read METADATA, WHEEL and
RECORD and checked existence and byte size for every RECORD path. The 15 entries
below have no missing paths or size mismatch. They are candidate reusable
unpacked archives, not downloaded wheel files or installed packages. No payload
hash verification or package import was performed; these checks do not establish
byte integrity, official-artifact identity, or future uv reuse across index keys.
Listed byte counts sum RECORD-listed existing files, not compressed transfer size.
The complete cache-key paths and WHEEL/Requires-Dist text are in `archives.json`.

| Package/version | RECORD bytes | Archive suffix under archive-v0 |
| --- | ---: | --- |
| filelock==3.32.5 | 354,810 | `3ygzCs2WReveqCTa` |
| fsspec==2026.7.0 | 752,431 | `Or0xH1nL920_hs7w` |
| jinja2==3.1.6 | 496,892 | `x9A3tgQjPl2jR85N` |
| markupsafe==3.0.3 | 67,188 | `u-TFUJvyPyY-_0d4` |
| mpmath==1.3.0 | 1,950,197 | `rKoQNEekBWMOMrWd` |
| networkx==3.6.1 | 7,038,619 | `Zt8_gsgcHvEQhDST` |
| numpy==1.26.3 | 63,765,497 | `nps7Qoc0bpiVQJUT` |
| nvidia-cuda-cupti-cu11==11.8.87 | 41,665,030 | `K4C9OHp-HhuUuBZZ` |
| nvidia-cuda-runtime-cu11==11.8.89 | 4,577,344 | `977t2vgSm8FLnlOu` |
| nvidia-cudnn-cu11==9.1.0.70 | 1,021,886,314 | `fRgg9pFTxE3dnKJP` |
| nvidia-nccl-cu11==2.21.5 | 192,411,259 | `Bgk0_JX29jYtlsvB` |
| nvidia-nvtx-cu11==11.8.86 | 416,586 | `iuqemiHkI6QvMSJ9` |
| setuptools==84.0.0 | 2,773,629 | `aF2TOAGAfML3NNRc` |
| sympy==1.14.0 | 26,841,861 | `_KWagnbFIqQeBAgJ` |
| typing-extensions==4.16.0 | 182,767 | `SKH_pC94xelcbakO` |

Torch 2.7.0+cu118 and Triton 3.3.0 have completed **cp310** archive entries,
whereas this path requires **cp312**. They are excluded. Six NVIDIA packages
have cached manylinux2014 builds but A02 selected manylinux1 builds; those
alternatives are likewise excluded, preserving the no-build-substitution
boundary. No claim of their binary equivalence is made. Matching NumPy is
cp312/cp312 manylinux_2_17+manylinux2014; matching MarkupSafe is cp312/cp312
manylinux_2_17+manylinux2014+manylinux_2_28. Pure-Python and matching NVIDIA tags
are retained as read from WHEEL.

For the eight exact missing wheels, inspected version/package cache entries
contain metadata/lock files or incompatible alternatives, without a completed
matching archive link. Metadata and zero-byte locks are not wheel payloads.
Unidentified partial download state is not counted as reusable or subtracted
from required acquisition. No partial/cache cleanup or extraction was attempted.

## Exact missing artifacts and current availability

One HEAD request per URL below, curl `--head --location --max-time 15`, at most
four concurrent requests. All returned final HTTP 200 with the Content-Length
shown; wheel response bodies were not requested. URLs came from the recorded
A02 installer, including its official PyTorch download-r2 host. The existing
profile's localhost/default-gateway algorithm selected HTTP proxy
`127.0.0.1:7890`; no profile was sourced and no new route was invented.
HEAD latencies are retained as inspection facts only, never throughput estimates.

| Exact wheel | Content-Length bytes |
| --- | ---: |
| [nvidia_cublas_cu11-11.11.3.6-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_cublas_cu11-11.11.3.6-py3-none-manylinux1_x86_64.whl) | 417,870,452 |
| [nvidia_cuda_nvrtc_cu11-11.8.89-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_cuda_nvrtc_cu11-11.8.89-py3-none-manylinux1_x86_64.whl) | 23,173,264 |
| [nvidia_cufft_cu11-10.9.0.58-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_cufft_cu11-10.9.0.58-py3-none-manylinux1_x86_64.whl) | 168,405,414 |
| [nvidia_curand_cu11-10.3.0.86-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_curand_cu11-10.3.0.86-py3-none-manylinux1_x86_64.whl) | 58,124,493 |
| [nvidia_cusolver_cu11-11.4.1.48-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_cusolver_cu11-11.4.1.48-py3-none-manylinux1_x86_64.whl) | 128,240,842 |
| [nvidia_cusparse_cu11-11.7.5.86-py3-none-manylinux1_x86_64.whl](https://download.pytorch.org/whl/cu118/nvidia_cusparse_cu11-11.7.5.86-py3-none-manylinux1_x86_64.whl) | 204,126,221 |
| [torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl](https://download-r2.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl) | 955,455,844 |
| [triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl](https://download-r2.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl) | 156,503,769 |

Availability is metadata-level only: an HTTP 200 header neither guarantees a
complete future body nor repairs A02's TLS response-body failure. No new package
source, Python version, NumPy/Torch pin or dependency/build substitution follows.

## One route and the remaining complete-invocation gap

The concrete unchanged-binary candidate route is to retain the 15 matching
archive candidates, acquire the eight exact bodies above from their existing
official URLs, and install the complete original 23-package closure into a
freshly selected task-local system-CPython 3.12 environment using lexical Python.
All necessary acquisition, any cache materialization/transfer, install, sole
metadata import and JSON publication/readback would belong inside the same
fresh adjacent-admitted <=600s invocation. No outside-cap wheel staging or
preparatory installation is proposed. This receipt does not freeze that command.

Optimistic remaining acquisition is 2,111,900,299 bytes **if** all 15 archive
candidates can be reused without acquisition; otherwise additional bytes are
required. Those extra bytes and cache acceptance are unresolved, not zero.
Even with zero setup/unpack/install/import/publication cost, transferring this
known lower bound in 600s requires 3.3568 MiB/s. At the prior 540s work deadline
it requires 3.7298 MiB/s, again leaving zero time for other required work.
Neither rate has been measured. A02's 104.11s failed transfer and 5.40s resolution
do not establish successful throughput or a complete 600s path. Installation,
import and publication remain unmeasured. No useful full-invocation upper bound
can therefore be asserted; launching now would repeat the unresolved acquisition
assumption. No extra profiling or wheel acquisition was performed to fill it.

The returnable technical dependency is thus the exact eight-wheel acquisition
plus verified reuse/installation/publication cost within the cap. It includes
the missing 955,455,844-byte cp312 Torch body and 156,503,769-byte cp312 Triton
body even if every compatible NVIDIA dependency could otherwise be reused.
No offline-complete route was found in the scoped existing state. DM owns any
next selection or return to Portfolio; no A03 or B04 invocation follows this
inspection receipt automatically.

## Recorded inspection work and return ownership

Five remote stdlib control-script reads covered: partial venv/cache headings and
selected A02 log lines; wheel index headings; exact package cache paths;
archive metadata/RECORD path sizes; eight bounded HEAD requests. Their observed
SSH-command walls were approximately 0.958, 0.658, 0.713, 1.114 and 3.464 seconds;
these are inspection costs, not preparation-run measurements. Local stdlib
parsing calculated byte totals and the conditional rate lower bounds. There
were zero installs, candidate imports, environment creations, full-wheel
acquisitions/transfers, host/model/RNG/optimizer/learner/evaluation calls, and
no new result-bearing run. All prior partial state and evidence remain intact.

Compact outputs and exact retained inspection scripts are in
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906/temp/directions/capability_bound_semantic_currentness/exp/a03_dependency_inspection_20260907/`:
`cache_paths.json`, `archives.json`, `availability.json`, `summary.json`,
`cache_inspection.py`, `archive_inspection.py`, `availability_inspection.py`.
Headers omit response cookies. These are task-local evidence files, not a new
cache manager, registry or runner. Only this receipt is committed. Git diff
whitespace check passes; no source or test changes require a suite.

Writer/index ownership returns to DM with the pushed receipt. Any later selected
command must return through CM preparation and Root integration before the sole
fresh admitted execution, as the handoff requires.
