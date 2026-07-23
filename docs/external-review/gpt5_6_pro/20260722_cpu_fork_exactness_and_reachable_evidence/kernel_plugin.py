"""pytest plugin: classify the CPU fork mismatch under Pro's Case A/B/C.

Pro's ruling requires the *decision-producing kernel* to be compared exactly,
not the stored likelihoods that are proxies for it. The event/mark decision
kernel is `_row_stable_event_heads` -> (logits, mark_output), with
mu, sigma = _normal_parameters(mark_output) a pure function of mark_output.

Method: every call, for every row, key on the exact bytes of
(input_row, event_head.weight, event_head.bias, mark_head.weight,
mark_head.bias). Identical key = identical mathematical query. Record the exact
output bytes. If the same key is ever evaluated at two different packed widths
and the output bytes differ, the kernel is width-dependent and the fork is
invalid (Case C). If the bytes always agree, the decision kernel is exact and
the mismatch lives only in post-decision derived arithmetic (Case B-benign).

This also records the widths actually observed, so "never compared at two
widths" is distinguishable from "compared and agreed" -- a vacuous pass would
otherwise read as evidence.
"""

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import torch

import ha_ctse_process.event_held_commitment_link as ehc

REPORT_PATH = Path(
    os.environ.get("KERNEL_REPORT_JSON", "kernel_exactness.json")
)
_original = ehc._row_stable_event_heads

# key -> {"widths": {width: output_digest}, "row_index": ..}
_observations: dict[str, dict] = {}
_violations: list[dict] = []
_calls = 0
_width_histogram: dict[int, int] = defaultdict(int)


def _digest(tensor: torch.Tensor) -> str:
    return hashlib.sha256(
        tensor.detach().contiguous().cpu().numpy().tobytes()
    ).hexdigest()[:32]


def _patched(inputs, event_head, mark_head):
    global _calls
    logits, mark_output = _original(inputs, event_head, mark_head)
    _calls += 1
    width = int(inputs.shape[0])
    _width_histogram[width] += 1
    parameter_key = _digest(
        torch.cat([
            event_head.weight.reshape(-1), event_head.bias.reshape(-1),
            mark_head.weight.reshape(-1), mark_head.bias.reshape(-1),
        ])
    )
    for row in range(width):
        key = f"{parameter_key}:{_digest(inputs[row])}"
        mu, sigma = ehc._normal_parameters(mark_output[row : row + 1])
        out = f"{_digest(logits[row])}:{_digest(mu)}:{_digest(sigma)}"
        record = _observations.setdefault(key, {"widths": {}})
        previous = record["widths"].get(str(width))
        if previous is None:
            record["widths"][str(width)] = out
        elif previous != out:
            _violations.append({
                "kind": "same_width_nondeterminism",
                "key": key, "width": width,
            })
        for other_width, other_out in record["widths"].items():
            if int(other_width) != width and other_out != out:
                _violations.append({
                    "kind": "width_dependent_kernel",
                    "key": key,
                    "width_a": int(other_width), "digest_a": other_out,
                    "width_b": width, "digest_b": out,
                })
    _write()
    return logits, mark_output


def _write() -> None:
    compared = {
        key: sorted(int(w) for w in record["widths"])
        for key, record in _observations.items()
        if len(record["widths"]) > 1
    }
    REPORT_PATH.write_text(
        json.dumps(
            {
                "torch": torch.__version__,
                "head_calls": _calls,
                "distinct_input_rows": len(_observations),
                "width_histogram": {str(k): v for k, v in sorted(_width_histogram.items())},
                "rows_evaluated_at_multiple_widths": len(compared),
                "multi_width_examples": dict(list(compared.items())[:10]),
                "violation_count": len(_violations),
                "violations": _violations[:20],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


ehc._row_stable_event_heads = _patched
_write()
