"""One retained-input ownership/allocator regression, without scientific construction."""
import base64
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.models import exact_binary64_mean
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import _ExactRosterMean


def test_retained_input_owned_mean_256_applications():
    torch.set_num_threads(1)
    root = Path(__file__).resolve().parents[4]
    record = json.loads((root / "docs/research/candidates/variable_n_fleet_churn/evidence/"
                        "b02_credit_20260911_01/repair_primitive_check.json").read_text())
    raw = base64.b64decode(record["core_input"]["data_base64"])
    prior = json.loads(record["primitive_stdout"])
    assert hashlib.sha256(raw).hexdigest() == prior["input_sha256"]
    matrix = np.frombuffer(raw, dtype=np.float64).reshape(7, 64)
    expected = exact_binary64_mean(matrix)
    assert hashlib.sha256(expected.tobytes()).hexdigest() == prior["output_sha256"]
    original = torch.tensor(np.broadcast_to(matrix, (24, 7, 64)).copy(), dtype=torch.float64)
    rows = original.clone().requires_grad_()
    expected_output = torch.tensor(np.broadcast_to(expected, (24, 64)).copy(), dtype=torch.float64)
    expected_gradient = torch.full_like(rows, 1.0 / 7.0)
    completed = 0
    for _ in range(256):
        result = _ExactRosterMean.apply(rows)
        assert result.shape == (24, 64) and result.dtype == torch.float64
        assert torch.equal(result, expected_output)
        result.sum().backward()
        assert rows.grad.shape == rows.shape and torch.equal(rows.grad, expected_gradient)
        assert torch.equal(rows.detach(), original)
        rows.grad = None
        completed += 1
    print(json.dumps({"completed_forward_backward_applications": completed,
                      "retained_input_sha256": prior["input_sha256"],
                      "mean_sha256": prior["output_sha256"],
                      "input_shape": list(rows.shape), "optimizer_steps": 0,
                      "model_instances": 0, "environment_instances": 0,
                      "scientific_rng_calls": 0, "torch": torch.__version__,
                      "numpy": np.__version__, "threads": torch.get_num_threads()}))
