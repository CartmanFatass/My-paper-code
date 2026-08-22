from datetime import datetime, timezone

from tools.hmasd_control_plane.resource_preflight import ResourceSnapshot, validate_resource_preflight


def snapshot(**kwargs):
    fields = dict(preflight_id="resource-1", assignment_id="asg-1", captured_at=datetime.now(timezone.utc).isoformat(), host_identity="host", route_id="r", backend="cpp", physical_cores=4, logical_processors=8, cpu_load_percent=20.0, total_memory_gib=16.0, available_memory_gib=8.0, selected_worker_count=3, threads_per_worker=1, parallel=True, selection_rationale="CM selected from current host memory", cm_owner="CM:x")
    fields.update(kwargs)
    return ResourceSnapshot(**fields)


def test_preflight_has_no_default_worker_count():
    assert not hasattr(snapshot(), "default_worker_count")


def test_preflight_records_cpu_memory_and_validates():
    assert validate_resource_preflight(snapshot()) == []


def test_oversubscription_needs_explanation():
    errors = validate_resource_preflight(snapshot(selected_worker_count=10))
    assert any("oversubscription" in error.lower() for error in errors)
