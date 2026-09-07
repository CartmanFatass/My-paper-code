# CBSC A03 dependency-path inspection receipt

**Corrected return: a concrete prospective same-version cache/acquisition route.**
Under DM's focused correction, reuse 21 compatible same-version archive entries,
including six existing NVIDIA cu11 manylinux2014 builds. Only cp312 Torch and
Triton bodies remain: **1,111,959,613 bytes** (1060.447 MiB). Materialize local
wheel containers from retained archive bytes, acquire those two official bodies,
and install the complete pinned closure within one future capped invocation.
This is a practical candidate for DM's bounded A03 selection, with uncertain
transfer/materialization/import time; it is not a proven runtime upper bound.
No installation, wheel materialization/acquisition or candidate import ran here.

The initial exact-A02-filename calculation (2,111,900,299 bytes) is retained below
as a narrower artifact comparison. It is **not** A03's required acquisition and
its earlier interpretation as a cost/launch gate is superseded by this correction.
A02's historical artifacts/results remain unchanged. No binary-equivalence,
B04-repair, version, CPU/CUDA-build or numerical-precision change is claimed.

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
alternatives were excluded only from the initial exact-A02-filename accounting.
The corrected prospective route below includes all six under DM clarification. No claim of their binary equivalence is made. Matching NumPy is
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

## Corrected prospective route: compatible same-version cache reuse

DM explicitly clarified that a new A03 may declare compatible same-version
transitive artifacts, rather than inheriting each A02 manylinux filename. The
six entries below all report `py3-none-manylinux2014_x86_64`, the same required
cu11 package versions and matching RECORD path sizes. These tags are compatible
with the same Ubuntu 24.04 x86_64/system-CPython3.12 host. None requires a cp310
ABI. Only cusolver lists an additional dependency (`nvidia-cublas-cu11`), already
in the closure. This is static structural/platform eligibility, not an import or
numerical-equivalence observation.

| Newly included same-version archive | RECORD bytes | Archive suffix |
| --- | ---: | --- |
| nvidia-cublas-cu11==11.11.3.6 | 670,513,157 | `4j5wtSN9ArOA5t3c` |
| nvidia-cuda-nvrtc-cu11==11.8.89 | 62,343,256 | `uozfOKGggobSVPcS` |
| nvidia-cufft-cu11==10.9.0.58 | 280,889,731 | `VB3V9onBAvFBaVJX` |
| nvidia-curand-cu11==10.3.0.86 | 103,501,780 | `2kcb46cD97jVRzCZ` |
| nvidia-cusolver-cu11==11.4.1.48 | 491,094,697 | `_QuNW0YQSjg48MLF` |
| nvidia-cusparse-cu11==11.7.5.86 | 280,298,557 | `5GJqvphDav2OfUnC` |

Origins are disclosed as actual retained local cache entries under
`/home/wu/.cache/uv/wheels-v6/index/fc5d3190421f7703/<package>/<version>-py3-none-manylinux2014_x86_64`
pointing to the archive suffixes above. The adjacent `.rev` bytes name the matching
wheel filename and archive ID; their hash arrays are empty and they contain no
origin URL. No remote origin URL or integrity certificate is invented. Existing
METADATA/WHEEL/RECORD evidence supports using these as local cache inputs for
a bounded candidate; absence of a certificate is not an added launch gate.

**One expressible route, entirely inside any later selected invocation:**

1. After adjacent resource admission, create the newly selected task-local
   system-CPython3.12 venv and a task-local wheel directory. Keep lexical Python.
2. Materialize the 21 listed compatible archive candidates as wheel ZIP files
   using existing system-Python stdlib `zipfile.ZipFile(..., compression=ZIP_STORED)`.
   Use each package's actual matching version/tags as its wheel filename and
   retain every RECORD-listed path with its bytes, including original METADATA,
   WHEEL and RECORD. No source build, compilation, precision change, cache edit
   or new package manager is involved. This local wheel-container packaging
   avoids assuming uv recognizes a cache entry from another index bucket.
   The selected archives contain 3,253,821,602 RECORD-file bytes; wheel output
   needs that space plus ZIP directory/header overhead. No such files exist
   from this inspection; all materialization cost belongs to the future cap.
3. Acquire the exact official cp312 Torch and Triton wheels below into that
   same task-local directory using existing download tooling within the cap.
4. Run existing uv once with `pip install --python <lexical-venv-python>
   --no-index --find-links <task-local-wheel-directory> --only-binary :all:` and
   all 23 selected package/version requirements from this receipt. Resolve the
   full dependency closure normally; do not use `--no-deps` or substitute cp310
   archives. Then run the sole selected metadata import and JSON publication/
   readback. Exact shell/quoting and resource details belong to later CM command
   preparation after DM selection and before Root integration.

The installed uv help confirms local `--find-links`, `--no-index`, binary-only,
explicit interpreter and cache-link modes. The container-packaging step uses
existing stdlib support; it introduces no standing helper/framework. It preserves
archive payload bytes but makes new ZIP container bytes, not a claim of identical
historical wheel bytes. No execution was used to validate this prospective route.

| Required remaining body | Bytes |
| --- | ---: |
| [torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl](https://download-r2.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl) | 955,455,844 |
| [triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl](https://download-r2.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl) | 156,503,769 |

The two bodies total **1,111,959,613 bytes**. This is 999,940,686 bytes less than
the exact-A02-filename acquisition calculation. The 21 archive inputs require
local reads/materialization/install, not new network wheel-body acquisition.
Their full paths and counted bytes are in `prospective_reuse_summary.json`.

Practical judgment: this is a concrete, reduced-acquisition same-version route
worth presenting to DM for the one bounded A03 decision. The complete work is
routing/admission + venv + local ZIP materialization + two downloads + uv install
+ one metadata import/publication. Successful throughput, disk materialization
and import times remain unknown; A02's TLS failure is still relevant risk.
The 1060.447 MiB bodies alone would require 1.9638 MiB/s if the entire prior
540s work allowance were spent transferring, with no other work. That arithmetic
is a workload description, not a required throughput test, feasibility proof or
launch condition. Unknown runtime upper bounds and absent payload certificates
are not new A/B gates under evidence-spec 11.8.7-11.9. DM decides whether this
supported route justifies the bounded assessment, retaining all failure outcomes.
No download probe, wheel acquisition or installation is commissioned by this
receipt correction.

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
cache manager, registry or runner. The focused correction also read existing uv install help and the six adjacent
cache `.rev` files (no package imports or downloads). `reuse_origin_read.txt`
and `prospective_reuse_summary.json` retain those facts. Only this receipt is committed. Git diff
whitespace check passes; no source or test changes require a suite.

Writer/index ownership returns to DM with the pushed receipt. Any later selected
command must return through CM preparation and Root integration before the sole
fresh admitted execution, as the handoff requires.
