"""Width-invariance of the executed sampling CDF, broken down BY CALL SITE.

Answers the vacuity question directly: not merely "were rows compared at two
widths" but "were the PRIMITIVE sampler's rows compared at two widths".
"""
import hashlib, json, os, traceback
from collections import defaultdict
from pathlib import Path
import torch, torch.nn.functional as F

REPORT = Path(os.environ.get("CDF2_JSON", "cdf2.json"))
_original_functions = {
    "cumsum": torch.cumsum,
    "softmax": torch.softmax,
    "log_softmax": F.log_softmax,
}
_observations = defaultdict(lambda: defaultdict(dict))
_call_counts = defaultdict(int)
_violations = []
_instrumentation_errors = []

def tensor_digest(tensor):
    return hashlib.sha256(
        tensor.detach().contiguous().cpu().numpy().tobytes()
    ).hexdigest()[:24]

def site_of():
    for call_frame in reversed(traceback.extract_stack()):
        filename = Path(call_frame.filename).name
        if filename != "cdf2_plugin.py":
            return f"{filename}:{call_frame.lineno}"
    return "?"

def observe(operator, input_tensor, output_tensor, call_site):
    _call_counts[(operator, call_site)] += 1
    if input_tensor.dim() < 2 or input_tensor.shape != output_tensor.shape:
        return
    batch_width = int(input_tensor.shape[0])
    site_records = _observations[(operator, call_site)]
    for row_index in range(batch_width):
        input_digest = tensor_digest(input_tensor[row_index])
        output_digest = tensor_digest(output_tensor[row_index])
        for prior_width, prior_output_digest in site_records[input_digest].items():
            if prior_output_digest != output_digest:
                _violations.append({
                    "op": operator,
                    "site": call_site,
                    "key": input_digest,
                    "w_a": prior_width,
                    "w_b": batch_width,
                })
        site_records[input_digest][batch_width] = output_digest

def wrap(operator, original_function):
    def wrapped_call(*args, **kwargs):
        result = original_function(*args, **kwargs)
        observation_site = "<site-unavailable>"
        try:
            if (
                args
                and isinstance(args[0], torch.Tensor)
                and isinstance(result, torch.Tensor)
            ):
                observation_site = site_of()
                observe(operator, args[0], result, observation_site)
        except Exception as instrumentation_error:
            _instrumentation_errors.append({
                "type": type(instrumentation_error).__name__,
                "message": str(instrumentation_error),
                "operator": operator,
                "site": observation_site,
            })
            raise
        return result
    return wrapped_call

torch.cumsum = wrap("cumsum", _original_functions["cumsum"])
torch.softmax = wrap("softmax", _original_functions["softmax"])
F.log_softmax = wrap("log_softmax", _original_functions["log_softmax"])

def pytest_sessionfinish(session, exitstatus):
    per_op_site = {}
    for (operator, call_site), site_records in _observations.items():
        multi_width_rows = {
            input_digest: sorted(width_outputs)
            for input_digest, width_outputs in site_records.items()
            if len(width_outputs) > 1
        }
        widths = sorted({
            batch_width
            for width_outputs in site_records.values()
            for batch_width in width_outputs
        })
        per_op_site[f"{operator} @ {call_site}"] = {
            "calls": _call_counts[(operator, call_site)],
            "distinct_rows": len(site_records),
            "rows_compared_at_multiple_widths": len(multi_width_rows),
            "widths_seen": widths[:25],
            "example_multi_width_sets": list(multi_width_rows.values())[:3],
        }
    is_valid = not _instrumentation_errors
    REPORT.write_text(json.dumps(
        {"torch": torch.__version__, "per_op_site": per_op_site,
         "violation_count": len(_violations), "violations": _violations[:20],
         "valid": is_valid, "status": "valid" if is_valid else "invalid",
         "instrumentation_errors": _instrumentation_errors},
        indent=2), encoding="utf-8")
    if not is_valid and session.exitstatus == 0:
        session.exitstatus = 1
