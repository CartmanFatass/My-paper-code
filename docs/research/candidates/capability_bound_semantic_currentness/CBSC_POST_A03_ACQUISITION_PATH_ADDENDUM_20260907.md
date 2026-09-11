# CBSC post-A03 acquisition-path addendum

**Proposal only: change the two body endpoints from download-r2.pytorch.org to
its observed official download.pytorch.org counterparts, retaining the same
package versions/tags and metadata goal.** Two bounded HEAD reads support a
material endpoint/CDN change. They do not establish complete body delivery,
byte identity, throughput or a complete runtime upper bound. DM/Portfolio may
consider one bounded candidate; this addendum commissions no invocation or A04.

## Assignment and retained boundary

P09-CBSC-NEXT-PATH-02 in the current Portfolio handoff and row104 supplies this
preparation. Shared `codex/cbsc` checkout began clean at `e43f2ad4a`; CM owns only
this addendum and returns writer/index ownership with its push. A03 source/card,
terminal/intake/E0 integrated at `e4612f518`, cache inputs,21containers and the
partial Torch file remain unchanged. Engineering-scope section4 additions:none.

A03's original curl used `-q --fail --location --retry 0` through the existing
localhost7890 HTTP proxy, targeting download-r2.pytorch.org. It terminated18
with a partial Torch body16027328/955455844bytes after21container materializations;
Triton, offline installation and metadata never ran. Whole9.65s remains within
its600s cap. No unique network/proxy/server/B04 cause follows from that exit.

The retained inventory records21container files totaling3,254,401,676bytes.
They may be read from the old output root by the proposed new invocation;
none is repackaged, overwritten or moved. The partial Torch file is preserved
and explicitly excluded from the prospective wheel input directory. No resume,
range request, segmented downloader, retry framework or alternate package is used.

## One alternative and actual metadata evidence

Inspection made exactly two HEAD-only requests, one per URL below, sequentially
through the already observed `http://127.0.0.1:7890` proxy. Commands used existing
curl `-q --head --location --retry 0 --max-time 12`; no wheel/range body was
requested. Both returned exit0, final HTTP/2 200 and final URL unchanged.
The combined SSH/read wall was3.504s. No additional network read or census ran.

| Selected wheel body | Observed length |
| --- | ---: |
| [torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl](https://download.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl) | 955,455,844 |
| [triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl](https://download.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl) | 156,503,769 |

Both responses identify AmazonS3 and CloudFront, unlike the retained R2 endpoint
headers identifying Cloudflare. Neither HEAD redirected to R2. The headers also
supply checksum metadata (retained in the compact evidence), but no wheel bytes
were acquired or hashed and no equivalence certificate is claimed. Same filenames,
versions, tags and lengths are the concrete same-package evidence. Differing
ETag/Last-Modified values are retained and not interpreted as an algorithm change.

This is a changed delivery endpoint, not a repetition of the A03 literal request.
The proxy, curl implementation, versions/tags, sequential/no-retry policy and
metadata goal stay fixed. Import failure, another partial transfer or cap expiry
remain possible. Headers are not success or speed evidence. No HTTP-version tweak,
new service, credentials or global configuration change is bundled into the proposal.

## Complete candidate work and timing

Retain all23pins, the21selected cache variants and cp312 Torch/Triton. Use a fresh
proposed candidate/output root; create21task-local symlinks to the retained complete
containers, with two new body files in the new directory. Symlinks expose only
those21named old files; the old partial Torch never enters the offline resolver.
Read-only old containers save the prior3.25GB materialization work without creating
an uncharged acquisition phase. Both whole bodies still require acquisition:
**1,111,959,613bytes**. Nothing is subtracted for the old partial body.

The one envelope includes shell/environment setup, adjacent actual-node admission,
venv/symlink creation, both sequential complete downloads, one full-dependency
binary offline uv install and one NumPy/Torch metadata process plus JSON readback.
Task-local UV cache/tmp retain writes; originals stay read-only. All acquisition
and installation must occur inside that same invocation if later commissioned.
One600s complete cap, existing GNU timeout KILL540s, no grace/restart. Actual
whole time decides conformance. Data transfer, local installation and import cost
remain uncertain; this concrete reduced-local-work endpoint candidate is plausible
for bounded consideration, not a demonstrated runtime upper bound. No throughput
probe or integrity proof is imposed as an A/B launch gate.

## Exact prospective command — not authorized to run

Proposed handle `cbsc-post-a03-acquisition-proposal-20260907`, node wsl_4070,
existing agent-task direct-command route. Proposed detached source worktree
`/home/wu/hmasd-worktrees/cbsc-post-a03-acquisition-proposal-20260907` uses already integrated `ec8866b3968fcb1566976ce405d7c552d4d9a5de`
for the unchanged resource preflight; that SHA is emitted only as `preflight_source_sha`.
The literal payload below is new in this addendum. Any future selection must
separately bind this exact committed addendum/payload as its command source; the
preflight SHA does not identify that command source. Proposed paths name no allocated object, and none was created.
A later selection must explicitly commission this command and the existing Root
integration/admission/observation route. No launch follows this push.

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

The metadata code preserves the accepted A03 checks for systemCPython3.12.3,
all23versions, NumPy/Torch paths and CUDA11.8, changing the descriptive
proposal object label and naming the unchanged preflight revision
`preflight_source_sha`, rather than claiming it identifies the new command. metadata_matches is never a substitute for actual complete
wall and publication. No tensor, device test, host, model, scientific RNG,
optimizer, learner or evaluator call is present. Body failure ends the command;
there is no follow-on acquisition or install after a failed sequential step.

## Check and return

Local compile parsed the two embedded Python programs without executing either;
shell payload/argv quoting was inspected. This is source preparation, not runtime
validation. Zero full-body/range downloads, packaging, installation, candidate
imports or result-bearing calls occurred. Existing21containers were not read
again; their retained terminal inventory supplies the exact symlink names.
No new child, branch, source edit or package/configuration framework was created.

Compact read-only outputs are under the shared checkout's
`temp/directions/capability_bound_semantic_currentness/exp/post_a03_path_20260907/`:
`head_inspection.py`, `alternative_headers.json`. Responses omit cookies.

Return recommendation: present this ONE changed endpoint candidate to DM/Portfolio
for future selection. It has concrete alternative endpoint support and preserved
complete work accounting, with delivery/timing uncertainty explicit. This does not
recommend an automatic A03 retry or infer scientific polarity. Writer/index
ownership returns to DM; Root integrates only this named addendum.

## DM assessment and recommendation — P09 preparation only

The original CM accepted the native P09 follow-up in the same shared checkout
and returned the proposal at `72e8bda2cad6e6b981b2a8625f878aa8e35e40ac`.
DM read the complete proposed command and its retained `alternative_headers.json`
against the P09 handoff's acceptance, plus the earlier `availability.json`.
One metadata-accuracy correction was returned to the same CM and completed at
`93520a182cbe7324d415457d3c2d5a19bd01daf3`: the old preflight revision is now
named `preflight_source_sha`, not falsely presented as the new inline payload's
source revision. No behavior, endpoint, package or bound changed in that correction.
DM inspected that exact diff without repeating CM checks or network requests.

Applied the preparation rule: one exact prospective command must account for
retained partial state, both missing bodies, installation/import/publication and
a complete <=600s cap, and explain its material difference, evidence and uncertainty.
This addendum meets that preparation requirement. It is not runtime acceptance.

The actual metadata evidence has two successful HEAD reads with final URLs still
on `download.pytorch.org`, AmazonS3/CloudFront headers, and exact selected lengths.
The retained R2 headers identify Cloudflare. This is concrete support for a
different delivery endpoint; no inference about successful complete bodies or
unique physical infrastructure is required. The two transfer lengths sum to
1,111,959,613 bytes by stdlib/Decimal calculation. The body-only 540-second
rate would be1.96379134MiB/s with zero other work, not a measured rate or cost proof.

Strongest contrary evidence: A02 also had body failures on `download.pytorch.org`
for other wheels, including `nvidia-cusolver-cu11`. The retained A02 install log
names its request at lines851–852 and terminal decoding/TLS failure at889–897:
`C:/Projects/HMASD-worktrees/cm-cbsc-runtime-a02-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a02_20260907/install.log`.
That different online uv/client/artifact attempt does not invalidate the present
curl/Torch/Triton candidate, but it prevents presenting CloudFront or the unchanged
proxy as known reliable. Another incomplete body remains a credible outcome.
Changing the delivery endpoint is not evidence that R2 caused A03 or that this
proposal repairs B04.

The prospective command reuses exactly21 named containers, excludes the retained
partial Torch file and allocates both complete bodies inside its one envelope.
It retains all23pins, full offline resolution, adjacent actual-node admission,
one metadata publication/readback and the600/540s complete-stop semantics. It
introduces no runtime source guard, retry or acquisition phase outside the cap.
None of the proposed paths, links, environment, bodies or metadata was created
during this preparation. Actual work was two bounded HEAD reads and static
preparation; body/installation/import/scientific counts remain zero.

**Options for later selection:** (a) use this one changed-endpoint command as the
next bounded candidate; (b) yield the acquisition dependency without another call.
**DM recommendation: (a).** A real endpoint alternative and the already materialized
inputs make this a sufficiently concrete candidate to return for consideration.
The proposal does not require a speed probe or identical-wheel proof before that
decision. Its complete runtime remains unknown, and yielding remains a Portfolio
allocation option. Known A01–A03 command work is740.50s with no ready candidate;
this preparation is not presumed cheaper than B04's53.46s RAW learning run.
The current-host tuned headroom record remains absent. Those facts limit the
investment case; they do not turn an untested delivery route into a scientific
negative or impose it as a prerequisite on unrelated learning.

**Executed choice: preparation only under P09-CBSC-NEXT-PATH-02.** Neither later
option is selected for execution by this return. No A04 card, invocation budget,
scientific prediction/result, direction disposition or Portfolio change is created.
The existing A03 intake, Chinese brief and owner-item outcome remain authoritative.
Current owner reviews were empty; no intervention or new owner reply is inferred.
Any later object selection must prospectively bind this committed command and its
inputs under the existing DM/Portfolio route, before an actual admitted call.

Root receives this single named addendum for integration and forwards the concrete
proposal/recommendation to Portfolio. The preparation task is complete; CM has
returned the editing/index window, and no live process or pending acquisition
remains. The next discriminator, if later selected, is the complete-body plus
installation/import outcome itself, with every failure retained.
