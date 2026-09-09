"""Typed native ground-geometry B01 adapter over the accepted UCOPE APIs."""

# These controls precede the first NumPy/Torch import on every package entry.
import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)
torch.set_default_device("cpu")

from .geometry import (
    DENSE,
    REL,
    DenseResidualEncoder,
    RelationResidualEncoder,
    NativeGeometryActor,
    build_pair,
    parameter_count,
)

__all__ = [
    "DENSE",
    "REL",
    "DenseResidualEncoder",
    "RelationResidualEncoder",
    "NativeGeometryActor",
    "build_pair",
    "parameter_count",
]
