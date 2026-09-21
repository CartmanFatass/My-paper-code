"""Read-only scale extraction from the complete, fixed B08 ordinary panels."""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import torch


REPO = Path(__file__).resolve().parents[4]
DEFINITION = Path(__file__).with_name("scales.json")


def extract(raw):
    with np.load(io.BytesIO(raw), allow_pickle=False) as arrays:
        means, previous = arrays["means"], arrays["previous"]
        if means.shape != (64, 256, 5, 3) or previous.shape != means.shape:
            raise ValueError("scale inputs must contain every declared B08 world/tick/agent")
        if means.dtype != np.float32 or previous.dtype != np.float32:
            raise TypeError("scale inputs must be FP32")
        if not np.isfinite(means).all() or not np.isfinite(previous).all():
            raise ValueError("scale inputs must be finite")
        # Same FP32 tanh, subtraction and reduction as B08's context construction.
        fresh = torch.tanh(torch.from_numpy(means[:, 1:].copy()))
        old = torch.from_numpy(previous[:, 1:].copy())
        distance = ((fresh - old).square().sum(-1) / 12).numpy().reshape(-1)
    q10, median, q90 = np.quantile(distance, [.1, .5, .9], method="linear")
    scale = float(q90 - q10)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("degenerate B08 distance scale; foundation cannot be dropped or rescaled")
    return {"rows": int(distance.size), "median": float(median), "q10": float(q10),
            "q90": float(q90), "scale": scale}


def load(master):
    definition_raw = DEFINITION.read_bytes()
    binding = json.loads(definition_raw)["masters"][str(master)]
    if binding["foundation_master"] != master - 20 or binding["source_master"] != master - 10:
        raise ValueError("scale-to-foundation identity mismatch")
    raw = (REPO / binding["source_npz"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["source_npz_sha256"]:
        raise ValueError("B08 scale input digest mismatch")
    actual = extract(raw)
    if any(actual[key] != binding[key] for key in actual):
        raise ValueError("fixed scale does not reproduce from its bound inputs")
    return dict(binding, definition_sha256=hashlib.sha256(definition_raw).hexdigest())
