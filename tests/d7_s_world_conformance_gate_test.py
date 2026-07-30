"""The gate's third outcome is the point: agreement is not automatically a pass.

Step 4 of the provenance correction. The ruling requires the check to be
cross-machine and says why:

    A test performed on one machine or one process is insufficient because that
    is precisely where the current generator appears stable.

So the gate must distinguish "agreed, on genuinely different runtimes" from
"agreed, and we cannot tell whether anything was tested". A two-outcome gate would
report PASS most confidently exactly when it had proven nothing -- the same shape
as a guard that cannot go red.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "d7_s_world_conformance_gate.py"

COMPONENTS = ("user_positions", "user_velocities", "user_waypoints",
              "user_pause_times", "user_cluster_assignments",
              "cluster_centers_history", "cluster_velocities",
              "cluster_waypoints", "cluster_pause_times")

RUNTIME_A = {"processor": "AMD64 Family 25", "machine": "AMD64", "platform": "Windows",
             "numpy_blas": {"name": "openblas64"}, "cpu_features": {"dispatch": ["AVX2"]}}
RUNTIME_B = {"processor": "Intel(R) Xeon(R) Platinum", "machine": "x86_64",
             "platform": "Linux", "numpy_blas": {"name": "openblas64"},
             "cpu_features": {"dispatch": ["AVX512F"]}}


def _sample(path, *, digests, runtime, seed=7):
    payload = {
        "runtime_identity": runtime,
        "episode_world_provenance": {"episode_worlds": [{
            "topology_seed": 20260734, "block": "audit", "episode_index": 0,
            "episode_seed": 11, "user_world_seed": seed,
            "pinned_coordinate_hash": "topo", "n_users": 3,
            "fingerprint": "fp", "component_digests": dict(digests),
        }]},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _run(a, b, *extra):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--samples", a, b, *extra],
                          capture_output=True, text=True, cwd=str(ROOT))
    return proc.returncode, proc.stdout + proc.stderr


BASE = {n: f"d_{n}" for n in COMPONENTS}


def test_agreement_on_distinct_runtimes_passes(tmp_path) -> None:
    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests=BASE, runtime=RUNTIME_B)
    code, out = _run(a, b)
    assert code == 0
    assert "WORLD_CONFORMANCE_PASS" in out
    assert "runtimes distinguishable: True" in out


def test_agreement_on_indistinguishable_runtimes_is_untested_not_pass(tmp_path) -> None:
    """THE POINT, and the paired negative for the pass path."""

    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests=BASE, runtime=dict(RUNTIME_A))
    code, out = _run(a, b)
    assert code == 1, "an untestable agreement must not exit zero"
    assert "WORLD_CONFORMANCE_UNTESTED" in out
    assert "WORLD_CONFORMANCE_PASS" not in out


def test_missing_runtime_identity_is_untested(tmp_path) -> None:
    a = _sample(tmp_path / "a.json", digests=BASE, runtime={})
    b = _sample(tmp_path / "b.json", digests=BASE, runtime={})
    code, out = _run(a, b)
    assert code == 1
    assert "WORLD_CONFORMANCE_UNTESTED" in out
    assert "records no runtime_identity" in out


def test_divergence_fails_and_names_the_earliest_component(tmp_path) -> None:
    moved = dict(BASE)
    moved["user_velocities"] = "CHANGED"        # index 1 in generation order
    moved["cluster_pause_times"] = "CHANGED"    # last
    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests=moved, runtime=RUNTIME_B)
    code, out = _run(a, b)
    assert code == 1
    assert "WORLD_CONFORMANCE_FAIL:user_velocities" in out
    assert "earliest in generation order: user_velocities" in out


def test_divergence_fails_even_on_the_same_runtime(tmp_path) -> None:
    """A difference is decisive whatever the hardware -- it proves non-determinism
    directly. Only AGREEMENT needs distinct runtimes to mean anything."""

    moved = dict(BASE, user_positions="CHANGED")
    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests=moved, runtime=dict(RUNTIME_A))
    code, out = _run(a, b)
    assert code == 1
    assert "WORLD_CONFORMANCE_FAIL:user_positions" in out


def test_identity_mismatch_is_untested(tmp_path) -> None:
    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A, seed=7)
    b = _sample(tmp_path / "b.json", digests=dict(BASE, user_positions="X"),
                runtime=RUNTIME_B, seed=8)
    code, out = _run(a, b)
    assert code == 1
    assert "WORLD_CONFORMANCE_UNTESTED" in out
    assert "user_world_seed" in out


def test_artifacts_without_digests_cannot_be_gated(tmp_path) -> None:
    """H and run 30479940700 are in this state."""

    a = _sample(tmp_path / "a.json", digests={}, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests={}, runtime=RUNTIME_B)
    code, out = _run(a, b)
    assert code == 1
    assert "WORLD_CONFORMANCE_UNTESTED" in out
    assert "component_digests" in out


def test_the_same_runtime_override_is_labelled_not_silent(tmp_path) -> None:
    """A development escape hatch must not be able to masquerade as a gate result."""

    a = _sample(tmp_path / "a.json", digests=BASE, runtime=RUNTIME_A)
    b = _sample(tmp_path / "b.json", digests=BASE, runtime=dict(RUNTIME_A))
    code, out = _run(a, b, "--allow-same-runtime")
    assert code == 0
    assert "WORLD_CONFORMANCE_PASS_SAME_RUNTIME_ALLOWED" in out
    assert "must not be cited as one" in out
