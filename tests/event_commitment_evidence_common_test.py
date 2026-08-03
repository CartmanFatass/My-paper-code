from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from ha_ctse_process import event_commitment_evidence_common
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


def _import_roots(source: str) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_common_owner_is_pure_and_runner_has_no_helper_reexports() -> None:
    helpers = {"_json_default", "_digest_json", "_is_exact_int"}
    common_source = Path(event_commitment_evidence_common.__file__).read_text(
        encoding="utf-8"
    )
    assert _import_roots(common_source) <= {
        "__future__", "hashlib", "json", "typing", "numpy", "torch"
    }

    runner_tree = ast.parse(Path(benchmark_runner.__file__).read_text(encoding="utf-8"))
    assert not {
        node.name for node in ast.walk(runner_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    } & helpers
    assert not {
        alias.name for node in ast.walk(runner_tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process.event_commitment_evidence_common"
        for alias in node.names
    }
    qualified = [
        node for node in ast.walk(runner_tree)
        if isinstance(node, ast.Attribute) and node.attr in helpers
    ]
    assert {node.attr for node in qualified} == helpers
    assert all(
        isinstance(node.value, ast.Name)
        and node.value.id == "event_commitment_evidence_common"
        for node in qualified
    )
    assert not {
        node.id for node in ast.walk(runner_tree)
        if isinstance(node, ast.Name) and node.id in helpers
    }


def test_canonical_json_digest_and_exact_int_behavior() -> None:
    value = {
        "tensor": torch.tensor([4, 5]),
        "word": "雪",
        "scalar": np.float32(3.5),
        "array": np.array([1, 2], dtype=np.int64),
    }
    canonical = b'{"array":[1,2],"scalar":3.5,"tensor":[4,5],"word":"\\u96ea"}'
    assert json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=event_commitment_evidence_common._json_default,
    ).encode("utf-8") == canonical
    assert event_commitment_evidence_common._digest_json(value) == hashlib.sha256(
        canonical
    ).hexdigest()
    assert event_commitment_evidence_common._is_exact_int(1)
    assert not event_commitment_evidence_common._is_exact_int(True)
    assert not event_commitment_evidence_common._is_exact_int(np.int64(1))
