#!/bin/bash
# One selected A03 preparation; outer time/timeout and cleared shell env are in the CM record.
set -euo pipefail
repo=$1
out=$2
candidate=$3
launch_sha=$4
cd "$repo"
export UV_CACHE_DIR="$out/uv-cache" TMPDIR="$out/tmp"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
if /usr/bin/curl -q -sI -m 1 http://127.0.0.1:7890 >/dev/null 2>&1; then
    host_ip=127.0.0.1
else
    host_ip=$(/usr/sbin/ip route | /usr/bin/awk '/default/ {print $3}')
fi
export http_proxy="http://${host_ip}:7890" https_proxy="http://${host_ip}:7890"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export no_proxy='localhost,127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8'
export NO_PROXY="$no_proxy"
/usr/bin/python3 scripts/hmasd_resource_preflight.py admit-memory --out "$out/admission.json" && {
    /usr/bin/mkdir -p "$out/wheels" "$out/tmp"
    /home/wu/.local/bin/uv --no-config venv --python /usr/bin/python3 --no-python-downloads "$candidate"
    /usr/bin/python3 - "$out/wheels" <<'PY_PACK'
import csv, sys, zipfile
from pathlib import Path
wheel_dir = Path(sys.argv[1])
archives = [('/home/wu/.cache/uv/archive-v0/3ygzCs2WReveqCTa', 'filelock-3.32.5-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/Or0xH1nL920_hs7w', 'fsspec-2026.7.0-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/x9A3tgQjPl2jR85N', 'jinja2-3.1.6-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/u-TFUJvyPyY-_0d4',
  'markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/rKoQNEekBWMOMrWd', 'mpmath-1.3.0-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/Zt8_gsgcHvEQhDST', 'networkx-3.6.1-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/nps7Qoc0bpiVQJUT',
  'numpy-1.26.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/K4C9OHp-HhuUuBZZ',
  'nvidia_cuda_cupti_cu11-11.8.87-py3-none-manylinux1_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/977t2vgSm8FLnlOu',
  'nvidia_cuda_runtime_cu11-11.8.89-py3-none-manylinux1_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/fRgg9pFTxE3dnKJP',
  'nvidia_cudnn_cu11-9.1.0.70-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/Bgk0_JX29jYtlsvB',
  'nvidia_nccl_cu11-2.21.5-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/iuqemiHkI6QvMSJ9',
  'nvidia_nvtx_cu11-11.8.86-py3-none-manylinux1_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/aF2TOAGAfML3NNRc', 'setuptools-84.0.0-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/_KWagnbFIqQeBAgJ', 'sympy-1.14.0-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/SKH_pC94xelcbakO', 'typing_extensions-4.16.0-py3-none-any.whl'),
 ('/home/wu/.cache/uv/archive-v0/4j5wtSN9ArOA5t3c',
  'nvidia_cublas_cu11-11.11.3.6-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/uozfOKGggobSVPcS',
  'nvidia_cuda_nvrtc_cu11-11.8.89-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/VB3V9onBAvFBaVJX',
  'nvidia_cufft_cu11-10.9.0.58-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/2kcb46cD97jVRzCZ',
  'nvidia_curand_cu11-10.3.0.86-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/_QuNW0YQSjg48MLF',
  'nvidia_cusolver_cu11-11.4.1.48-py3-none-manylinux2014_x86_64.whl'),
 ('/home/wu/.cache/uv/archive-v0/5GJqvphDav2OfUnC',
  'nvidia_cusparse_cu11-11.7.5.86-py3-none-manylinux2014_x86_64.whl')]
for source, filename in archives:
    source = Path(source)
    record = next(source.glob("*.dist-info/RECORD"))
    with record.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    with zipfile.ZipFile(wheel_dir / filename, "w", compression=zipfile.ZIP_STORED) as wheel:
        for relative, digest, size in rows:
            wheel.write(source / relative, relative)
    print("materialized", filename, (wheel_dir / filename).stat().st_size, flush=True)
PY_PACK
    /usr/bin/curl -q --fail --location --retry 0 --output "$out/wheels/torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl" https://download-r2.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl
    /usr/bin/curl -q --fail --location --retry 0 --output "$out/wheels/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl" https://download-r2.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
    /home/wu/.local/bin/uv --no-config pip install --python "$candidate/bin/python" --no-index --find-links "$out/wheels" --only-binary :all: filelock==3.32.5 fsspec==2026.7.0 jinja2==3.1.6 markupsafe==3.0.3 mpmath==1.3.0 networkx==3.6.1 numpy==1.26.3 nvidia-cublas-cu11==11.11.3.6 nvidia-cuda-cupti-cu11==11.8.87 nvidia-cuda-nvrtc-cu11==11.8.89 nvidia-cuda-runtime-cu11==11.8.89 nvidia-cudnn-cu11==9.1.0.70 nvidia-cufft-cu11==10.9.0.58 nvidia-curand-cu11==10.3.0.86 nvidia-cusolver-cu11==11.4.1.48 nvidia-cusparse-cu11==11.7.5.86 nvidia-nccl-cu11==2.21.5 nvidia-nvtx-cu11==11.8.86 setuptools==84.0.0 sympy==1.14.0 torch==2.7.0+cu118 triton==3.3.0 typing-extensions==4.16.0 > "$out/install.log" 2>&1
    "$candidate/bin/python" - "$out" "$launch_sha" "$candidate/bin/python" <<'PY_META'
import importlib.metadata as md
import json, platform, sys
from pathlib import Path
import numpy
import torch
expected = {'filelock': '3.32.5',
 'fsspec': '2026.7.0',
 'jinja2': '3.1.6',
 'markupsafe': '3.0.3',
 'mpmath': '1.3.0',
 'networkx': '3.6.1',
 'numpy': '1.26.3',
 'nvidia-cublas-cu11': '11.11.3.6',
 'nvidia-cuda-cupti-cu11': '11.8.87',
 'nvidia-cuda-nvrtc-cu11': '11.8.89',
 'nvidia-cuda-runtime-cu11': '11.8.89',
 'nvidia-cudnn-cu11': '9.1.0.70',
 'nvidia-cufft-cu11': '10.9.0.58',
 'nvidia-curand-cu11': '10.3.0.86',
 'nvidia-cusolver-cu11': '11.4.1.48',
 'nvidia-cusparse-cu11': '11.7.5.86',
 'nvidia-nccl-cu11': '2.21.5',
 'nvidia-nvtx-cu11': '11.8.86',
 'setuptools': '84.0.0',
 'sympy': '1.14.0',
 'torch': '2.7.0+cu118',
 'triton': '3.3.0',
 'typing-extensions': '4.16.0'}
versions = {name: md.version(name) for name in expected}
result = {
    "object": "CBSC-SYSTEM-RUNTIME-A03", "launch_sha": sys.argv[2],
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
