"""pytest plugin: localize the batched-audit natural-branch mismatch.

Wraps `_audit_row_errors` at the module attribute the call site resolves and
records, per nonzero continuous field, the stored/replayed values, the
coordinate, the float32 ULP at that magnitude and the ULP distance -- instead
of the single packed maximum the engine currently reports.
"""

import json
import os
from pathlib import Path

import torch

import ha_ctse_process.event_held_commitment_link as ehc

REPORT_PATH = Path(
    os.environ.get("FORK_LOCALIZATION_JSON", "fork_localization.json")
)
_original = ehc._audit_row_errors
_records: list[dict] = []


def _f32_ulp(magnitude: float) -> float:
    x = torch.tensor(abs(magnitude), dtype=torch.float32)
    up = torch.nextafter(x, torch.tensor(float("inf"), dtype=torch.float32))
    return float(up - x)


def _patched(branch, branch_index, original, original_env, *, start):
    out = _original(branch, branch_index, original, original_env, start=start)
    if out["continuous_error"] == 0.0:
        return out
    device = branch.rewards.device
    fields = []
    for name in ehc._AUDIT_CONTINUOUS_FIELDS:
        left = getattr(branch, name)[:, branch_index]
        right = getattr(original, name)[start:, original_env].to(device)
        if left.numel() == 0:
            continue
        diff = torch.abs(left - right)
        worst = float(torch.max(diff))
        if worst == 0.0:
            continue
        flat = diff.reshape(-1)
        idx = int(torch.argmax(flat))
        stored = float(right.reshape(-1)[idx])
        replayed = float(left.reshape(-1)[idx])
        magnitude = max(abs(stored), abs(replayed))
        ulp = _f32_ulp(magnitude) if magnitude > 0 else 0.0
        fields.append({
            "field": name,
            "dtype": str(left.dtype),
            "shape": list(diff.shape),
            "coordinate": [
                int(c) for c in torch.unravel_index(
                    torch.tensor(idx), tuple(diff.shape)
                )
            ],
            "stored_value": stored,
            "replayed_value": replayed,
            "absolute_error": worst,
            "max_abs_magnitude": magnitude,
            "float32_ulp_at_max_magnitude": ulp,
            "ulp_distance": (worst / ulp) if ulp > 0 else None,
            "nonzero_count": int((flat != 0).sum()),
            "element_count": int(flat.numel()),
        })
    _records.append({
        "packed_continuous_error": out["continuous_error"],
        "discrete_mismatch": out["discrete_mismatch"],
        "segment_equal": bool(out["segment_equal"]),
        "outcome_equal": bool(out["outcome_equal"]),
        "start": int(start),
        "branch_index": int(branch_index),
        "original_env": int(original_env),
        "nonzero_fields": fields,
    })
    _write()
    return out


def _write() -> None:
    REPORT_PATH.write_text(
        json.dumps(
            {
                "torch": torch.__version__,
                "audit_rows_with_nonzero_error": len(_records),
                "records": _records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


ehc._audit_row_errors = _patched
_write()
