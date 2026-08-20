"""Equivalence-gated benchmark for ``RNNLayer`` sequence backends.

The benchmark intentionally keeps the production implementation untouched.  It
uses cloned recurrent_N=1 layers and identical inputs to compare the reference
step loop with the segmented implementation, then alternates complete
forward/backward timings.  A successful process exit is a promotion gate, not
just a performance measurement.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time
from typing import Any

import numpy as np
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from hmasd.r_mappo_utils import RNNLayer


SCHEMA = "hmasd.rnn_sequence_backend_benchmark.v1"
FLOAT32_RTOL = 1e-6
FLOAT32_ATOL = 1e-7
BENCHMARK_SEED = 20260815


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_fingerprint(value: object) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _source_fingerprint() -> dict[str, str]:
    source = REPOSITORY_ROOT / "hmasd" / "r_mappo_utils.py"
    return {"path": source.relative_to(REPOSITORY_ROOT).as_posix(), "sha256": _sha256_bytes(source.read_bytes())}


def _machine_fingerprint(device: torch.device) -> dict[str, object]:
    value: dict[str, object] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
    }
    if device.type == "cuda":
        value["cuda"] = torch.version.cuda
        value["cuda_device"] = torch.cuda.get_device_name(device)
    value["sha256"] = _stable_fingerprint(value)
    return value


def _rng_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state().clone(),
    }
    if torch.cuda.is_available():
        snapshot["torch_cuda"] = [state.clone() for state in torch.cuda.get_rng_state_all()]
    return snapshot


def _restore_rng(snapshot: dict[str, Any]) -> None:
    random.setstate(snapshot["python"])
    np.random.set_state(snapshot["numpy"])
    torch.set_rng_state(snapshot["torch_cpu"])
    if "torch_cuda" in snapshot:
        torch.cuda.set_rng_state_all(snapshot["torch_cuda"])


def _rng_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left["python"] != right["python"]:
        return False
    left_numpy, right_numpy = left["numpy"], right["numpy"]
    if left_numpy[0] != right_numpy[0] or left_numpy[2:] != right_numpy[2:]:
        return False
    if not np.array_equal(left_numpy[1], right_numpy[1]):
        return False
    if not torch.equal(left["torch_cpu"], right["torch_cpu"]):
        return False
    left_cuda, right_cuda = left.get("torch_cuda", []), right.get("torch_cuda", [])
    return len(left_cuda) == len(right_cuda) and all(
        torch.equal(before, after) for before, after in zip(left_cuda, right_cuda)
    )


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _make_workload(
    *, device: torch.device, timesteps: int, batch_size: int, input_dim: int, hidden_size: int
) -> tuple[RNNLayer, RNNLayer, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    generator = torch.Generator(device=device)
    generator.manual_seed(BENCHMARK_SEED)
    # fork_rng makes the layer initialization deterministic without leaking a
    # seed change to the caller's CPU or CUDA RNG streams.
    cuda_devices = [device.index or 0] if device.type == "cuda" else []
    with torch.random.fork_rng(devices=cuda_devices):
        torch.manual_seed(BENCHMARK_SEED)
        reference = RNNLayer(
            input_dim, hidden_size, 1, True, sequence_backend="step_reference"
        ).to(device=device, dtype=torch.float32)
    segmented = copy.deepcopy(reference)
    segmented.sequence_backend = "segmented"
    x = torch.randn(
        timesteps, batch_size, input_dim, generator=generator, device=device, dtype=torch.float32
    )
    hxs = torch.randn(
        batch_size, hidden_size, generator=generator, device=device, dtype=torch.float32
    )
    masks = torch.ones(timesteps, batch_size, device=device, dtype=torch.float32)
    # Multiple independent reset boundaries exercise the segmented branch.
    for row in range(1, timesteps):
        if row % 3 == 0 or row == timesteps - 1:
            masks[row, row % batch_size] = 0.0
    loss_weight = torch.randn(
        timesteps, batch_size, hidden_size, generator=generator, device=device, dtype=torch.float32
    )
    return reference, segmented, x, hxs, masks, loss_weight


def _forward_backward(
    layer: RNNLayer,
    x: torch.Tensor,
    hxs: torch.Tensor,
    masks: torch.Tensor,
    loss_weight: torch.Tensor,
    *,
    retain_results: bool,
) -> dict[str, Any]:
    layer.zero_grad(set_to_none=True)
    x_input = x.detach().clone().requires_grad_(True)
    hxs_input = hxs.detach().clone().requires_grad_(True)
    output, final_hidden = layer(x_input, hxs_input, masks)
    loss = (output * loss_weight).sum() + final_hidden.square().sum()
    loss.backward()
    result: dict[str, Any] = {"checksum": float(loss.detach().cpu())}
    if retain_results:
        result.update(
            {
                "output": output.detach().clone(),
                "final_hidden": final_hidden.detach().clone(),
                "input_gradient": x_input.grad.detach().clone(),
                "hidden_gradient": hxs_input.grad.detach().clone(),
                "parameter_gradients": {
                    name: parameter.grad.detach().clone()
                    for name, parameter in layer.named_parameters()
                },
            }
        )
    return result


def _comparison(reference: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    for name in ("output", "final_hidden", "input_gradient", "hidden_gradient"):
        if not torch.allclose(reference[name], candidate[name], rtol=FLOAT32_RTOL, atol=FLOAT32_ATOL):
            mismatches.append(name)
    if set(reference["parameter_gradients"]) != set(candidate["parameter_gradients"]):
        mismatches.append("parameter_gradient_keys")
    else:
        for name, expected in reference["parameter_gradients"].items():
            if not torch.allclose(
                expected,
                candidate["parameter_gradients"][name],
                rtol=FLOAT32_RTOL,
                atol=FLOAT32_ATOL,
            ):
                mismatches.append(f"parameter_gradient:{name}")
    return mismatches


def _time_backend(
    layer: RNNLayer,
    x: torch.Tensor,
    hxs: torch.Tensor,
    masks: torch.Tensor,
    loss_weight: torch.Tensor,
    *,
    iterations: int,
    device: torch.device,
) -> float:
    _synchronize(device)
    started = time.perf_counter()
    checksum = 0.0
    for _ in range(iterations):
        checksum += _forward_backward(
            layer, x, hxs, masks, loss_weight, retain_results=False
        )["checksum"]
    _synchronize(device)
    if not np.isfinite(checksum):
        raise RuntimeError("RNN benchmark checksum is non-finite")
    return time.perf_counter() - started


def _production_default() -> str:
    return str(inspect.signature(RNNLayer.__init__).parameters["sequence_backend"].default)


def run_benchmark(
    *,
    repeats: int = 31,
    iterations: int = 20,
    timesteps: int = 32,
    batch_size: int = 16,
    input_dim: int = 64,
    hidden_size: int = 128,
    device: str = "cpu",
) -> dict[str, object]:
    """Run the bounded promotion gate without changing caller RNG state."""
    if repeats < 31 or repeats % 2 == 0:
        raise ValueError("benchmark requires an odd repeats value of at least 31")
    if min(iterations, timesteps, batch_size, input_dim, hidden_size) <= 0:
        raise ValueError("iterations and all workload dimensions must be positive")
    selected_device = torch.device(device)
    if selected_device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA benchmark requested but CUDA is unavailable")

    incoming_rng = _rng_snapshot()
    try:
        reference, segmented, x, hxs, masks, loss_weight = _make_workload(
            device=selected_device,
            timesteps=int(timesteps),
            batch_size=int(batch_size),
            input_dim=int(input_dim),
            hidden_size=int(hidden_size),
        )
        reference_result = _forward_backward(
            reference, x, hxs, masks, loss_weight, retain_results=True
        )
        segmented_result = _forward_backward(
            segmented, x, hxs, masks, loss_weight, retain_results=True
        )
        mismatches = _comparison(reference_result, segmented_result)

        for _ in range(3):
            _time_backend(reference, x, hxs, masks, loss_weight, iterations=1, device=selected_device)
            _time_backend(segmented, x, hxs, masks, loss_weight, iterations=1, device=selected_device)
        timings: dict[str, list[float]] = {"step_reference": [], "segmented": []}
        layers = {"step_reference": reference, "segmented": segmented}
        for repeat in range(repeats):
            order = ("step_reference", "segmented") if repeat % 2 == 0 else ("segmented", "step_reference")
            for name in order:
                timings[name].append(
                    _time_backend(
                        layers[name], x, hxs, masks, loss_weight,
                        iterations=int(iterations), device=selected_device,
                    )
                )
        reference_median = statistics.median(timings["step_reference"])
        segmented_median = statistics.median(timings["segmented"])
        positive_median = segmented_median < reference_median
    finally:
        outgoing_rng = _rng_snapshot()
        rng_preserved = _rng_equal(incoming_rng, outgoing_rng)
        _restore_rng(incoming_rng)

    oracle_equivalent = not mismatches
    gate_passed = bool(oracle_equivalent and rng_preserved and positive_median)
    config = {
        "seed": BENCHMARK_SEED,
        "repeats": int(repeats),
        "iterations": int(iterations),
        "timesteps": int(timesteps),
        "batch_size": int(batch_size),
        "input_dim": int(input_dim),
        "hidden_size": int(hidden_size),
        "dtype": "float32",
        "rtol": FLOAT32_RTOL,
        "atol": FLOAT32_ATOL,
        "backends": ["step_reference", "segmented"],
        "timing_scope": "forward_backward",
    }
    current_default = _production_default()
    return {
        "schema": SCHEMA,
        "bounded_workload": True,
        "source_fingerprint": _source_fingerprint(),
        "config": config,
        "config_fingerprint": _stable_fingerprint(config),
        "machine_fingerprint": _machine_fingerprint(selected_device),
        "numeric_equivalent": oracle_equivalent,
        "numeric_mismatches": mismatches,
        "rng_preserved": rng_preserved,
        "step_reference_median_seconds": reference_median,
        "segmented_median_seconds": segmented_median,
        "segmented_speedup": reference_median / segmented_median,
        "positive_median": positive_median,
        "gate_passed": gate_passed,
        "current_production_default": current_default,
        "production_default_if_gate_fails": "step_reference",
        "recommended_production_default": "segmented" if gate_passed else "step_reference",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--timesteps", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--input-dim", type=int, default=64)
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = run_benchmark(
        repeats=arguments.repeats,
        iterations=arguments.iterations,
        timesteps=arguments.timesteps,
        batch_size=arguments.batch_size,
        input_dim=arguments.input_dim,
        hidden_size=arguments.hidden_size,
        device=arguments.device,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    if not result["gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
