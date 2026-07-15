#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/root/autodl-tmp/HMASD}"
BASE_PYTHON="${BASE_PYTHON:-/root/miniconda3/bin/python3}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$DATA_ROOT/runtime/r41_official_hmasd}"

if [[ "$RUNTIME_ROOT" != "$DATA_ROOT"/runtime/* ]]; then
  echo "RUNTIME_ROOT must stay under $DATA_ROOT/runtime on the data disk." >&2
  exit 2
fi
if [[ ! -x "$BASE_PYTHON" ]]; then
  echo "BASE_PYTHON is not executable: $BASE_PYTHON" >&2
  exit 2
fi

if [[ ! -x "$RUNTIME_ROOT/bin/python" ]]; then
  "$BASE_PYTHON" -m venv --system-site-packages "$RUNTIME_ROOT"
fi

"$RUNTIME_ROOT/bin/python" -m pip install --upgrade pip
"$RUNTIME_ROOT/bin/python" -m pip install \
  'gym==0.12.4' \
  'tensorboardX==2.5' \
  'wandb==0.12.11' \
  'setproctitle==1.2.2' \
  'opencv-python-headless==4.5.5.64' \
  'matplotlib==3.5.1' \
  'absl-py'

"$RUNTIME_ROOT/bin/python" -c \
  'import torch, numpy, gym, tensorboardX, wandb, cv2, matplotlib, absl, setproctitle; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, gym.__version__)'

echo "R41_PYTHON=$RUNTIME_ROOT/bin/python"
