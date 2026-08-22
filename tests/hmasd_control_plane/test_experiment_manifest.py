from datetime import datetime, timezone
from pathlib import Path

from tools.hmasd_control_plane.experiment_manifest import ExperimentManifest, validate_manifest
from tools.hmasd_control_plane.requirements_registry import load_requirements
from tools.hmasd_control_plane.resource_preflight import ResourceSnapshot


def test_manifest_worker_count_matches_preflight(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs/project").mkdir(parents=True)
    (tmp_path / "docs/project/PROJECT_MAP.md").write_text("## Route\n", encoding="utf-8")
    for name in ("entry.py", "runner.py", "factory.py", "native.py", "consumer.py", "preflight.json"):
        (tmp_path / name).write_text("", encoding="utf-8")
    preflight = ResourceSnapshot("resource-x", "asg-x", datetime.now(timezone.utc).isoformat(), "host", "route", "cpp", 4, 8, 10.0, 16.0, 8.0, 3, 1, True, "CM selected from memory", "CM:x")
    manifest = ExperimentManifest("manifest-x", "asg-x", "B", "R2_EXPERIMENT_EXECUTION", "TOY_SMOKE", True, ("UR-EXEC-001", "UR-EXEC-002", "UR-RESOURCE-001", "UR-PERF-001"), ("NR-WORKER-LIMIT-001",), "preflight.json", "Route", "entry.py", "runner.py", "factory.py", "native.py", "consumer.py", "route", "cpp", True, 3, "RESOURCE_PREFLIGHT", 1, False, None)
    errors = validate_manifest(manifest, preflight, load_requirements(Path("C:/Projects/HMASD-low-intrusion-control-plane/docs/project/PROJECT_REQUIREMENTS.toml")), {"route": {"cpp_backend": "AVAILABLE", "parallel_execution": "AVAILABLE", "semantic_equivalence": "REGISTERED"}}, Path("docs/project/PROJECT_MAP.md"))
    assert not any("worker_count" in error for error in errors)


def test_debug_reference_may_be_serial_python(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs/project").mkdir(parents=True)
    (tmp_path / "docs/project/PROJECT_MAP.md").write_text("## Route\n", encoding="utf-8")
    for name in ("entry.py", "runner.py", "factory.py", "native.py", "consumer.py", "preflight.json"):
        (tmp_path / name).write_text("", encoding="utf-8")
    pre = ResourceSnapshot("resource-x", "asg-x", datetime.now(timezone.utc).isoformat(), "host", "route", "python", 4, 8, 10.0, 16.0, 8.0, 1, 1, False, "reference oracle", "CM:x")
    man = ExperimentManifest("m", "asg-x", "B", "R1_ROUTINE_ENGINEERING", "TOY_SMOKE", False, (), (), "preflight.json", "Route", "entry.py", "runner.py", "factory.py", "native.py", "consumer.py", "route", "python", False, 1, "RESOURCE_PREFLIGHT", 1, False, None)
    assert not any("result-bearing" in error for error in validate_manifest(man, pre, {}, {"route": {}}, Path("docs/project/PROJECT_MAP.md")))
