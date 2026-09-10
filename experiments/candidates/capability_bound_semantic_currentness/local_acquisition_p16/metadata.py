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
    "object": "CBSC-LOCAL-ACQUISITION-P16", "preflight_source_sha": sys.argv[2], "command_source_sha": sys.argv[4], "seed": int(sys.argv[5]),
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
