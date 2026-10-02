"""Byte/path binding checks only; no policy, native, RF or analytical query."""
from pathlib import Path
import pytest
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.contract import (
    ROOT, jobs, reference_evidence, reference_root_for_output,
)


def test_canonical_output_controls_reference_root():
    canonical = Path("/home/wu/projects/HMASD")
    output = canonical / "runs/uav_fleet_transmission/b12_resource_engineering_a01"
    assert reference_root_for_output(output) == canonical
    # A snapshot-relative source root is deliberately not an accepted substitute.
    with pytest.raises(ValueError, match="canonical"):
        reference_root_for_output(canonical / ".snapshots/source/b12_resource_engineering_a01")


@pytest.mark.parametrize("phase", ("engineering", "scientific"))
def test_frozen_compact_and_original_git_sources(phase):
    result = reference_evidence(ROOT, phase, verify_raw=False, verify_sources=True)
    seeds = {job["seed"] for job in jobs(phase)}
    assert {(r["seed"], r["arm"]) for r in result["rows"]} == {
        (seed, arm) for seed in seeds for arm in ("C", "H_A", "H_T")
    }
    assert len(result["groups"]) == 2
    assert result["new_controller_calls"] == result["new_model_calls"] == result["new_native_calls"] == 0
