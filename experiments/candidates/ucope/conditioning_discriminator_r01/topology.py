"""Once-only deterministic CPU topology and static no-spawn evidence."""

from __future__ import annotations

import ast
from pathlib import Path
import threading

_LOCK = threading.Lock()
_RECORD = None


def static_no_spawn_audit() -> dict[str, object]:
    root = Path(__file__).resolve().parent
    paths = tuple(root / name for name in ("workflow.py", "training.py", "assessment_v2.py"))
    forbidden = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                forbidden.extend(alias.name for alias in node.names if alias.name in {"multiprocessing", "subprocess", "concurrent.futures"})
            elif isinstance(node, ast.ImportFrom) and node.module in {"multiprocessing", "subprocess", "concurrent.futures"}:
                forbidden.append(node.module)
    if forbidden: raise ValueError(f"scientific core may not spawn workers: {forbidden}")
    return {"files_checked": len(paths), "spawn_imports": 0, "topology": "single_inline_root_process"}


def configure_torch_topology_once() -> dict[str, object]:
    global _RECORD
    with _LOCK:
        if _RECORD is not None: return dict(_RECORD)
        import torch
        torch.use_deterministic_algorithms(True)
        torch.set_num_threads(1)
        interop_supported = hasattr(torch, "set_num_interop_threads") and hasattr(torch, "get_num_interop_threads")
        if not interop_supported:
            raise RuntimeError("exact V3 topology requires torch interop thread support")
        if torch.get_num_interop_threads() != 1:
            try: torch.set_num_interop_threads(1)
            except RuntimeError as exc: raise RuntimeError("interop topology was not frozen before tensor work") from exc
        audit = static_no_spawn_audit()
        record = {
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "intraop_threads": int(torch.get_num_threads()),
            "interop_threads": int(torch.get_num_interop_threads()),
            "interop_supported": True,
            "configured_once": True,
            "static_no_spawn": audit,
        }
        if not record["deterministic_algorithms"] or record["intraop_threads"] != 1 or record["interop_supported"] is not True or record["interop_threads"] != 1: raise RuntimeError("deterministic CPU topology drift")
        _RECORD = record
        return dict(record)


def measured_worker_count(telemetry, topology_record) -> int:
    audit = topology_record.get("static_no_spawn", {})
    return 1 if telemetry.get("root_process_count") == 1 and telemetry.get("child_process_count_peak") == 0 and audit.get("spawn_imports") == 0 else 0
