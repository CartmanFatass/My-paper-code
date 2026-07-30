"""The localizer must find a real divergence, and refuse a meaningless one.

`scripts/d7_s_world_component_digest_diff.py` is step 1 of the provenance
correction ruled on 2026-07-30. Two properties carry the weight:

1. it reports the first differing array **in generation order**, not
   alphabetical order, because a divergence in an earlier array propagates into
   later ones through the shared RNG stream -- alphabetical order would name a
   consequence and call it the cause;
2. it REFUSES when the two sides' registered identity differs, because then the
   worlds are supposed to differ and a divergence proves nothing. That is the
   wrong-namespace error this research line has already made once, in
   `d7_s_r4_rejoin_exposure_probe.py`, where every derived seed differed and the
   verdict was reported anyway.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "d7_s_world_component_digest_diff.py"


def _load():
    spec = importlib.util.spec_from_file_location("_digest_diff", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOD = _load()

_COMPONENTS = MOD.COMPONENT_ORDER


def _world(block, index, *, digests, seed=7, fingerprint="fp"):
    return {
        "block": block, "episode_index": index, "episode_seed": 11,
        "user_world_seed": seed, "pinned_coordinate_hash": "topo", "n_users": 3,
        "fingerprint": fingerprint,
        "component_digests": dict(digests),
    }


def _artifact(path, worlds):
    path.write_text(json.dumps(
        {"episode_world_provenance": {"episode_worlds": worlds}}), encoding="utf-8")
    return str(path)


def _run(left, right, out=None):
    cmd = [sys.executable, str(SCRIPT), "--left", left, "--right", right]
    if out:
        cmd += ["--out", out]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return proc.returncode, proc.stdout + proc.stderr


def test_generation_order_is_not_alphabetical() -> None:
    """The premise. If these coincided, ordering by either would look correct and
    the script could name a consequence as the root cause without anyone noticing.
    """

    assert list(_COMPONENTS) != sorted(_COMPONENTS)
    assert _COMPONENTS[0] == "user_positions"


def test_identical_digests_report_no_divergence(tmp_path) -> None:
    base = {name: f"d_{name}" for name in _COMPONENTS}
    left = _artifact(tmp_path / "l.json", [_world("audit", 0, digests=base)])
    right = _artifact(tmp_path / "r.json", [_world("audit", 0, digests=base)])
    code, out = _run(left, right)
    assert code == 0
    assert "WORLD_COMPONENTS_IDENTICAL" in out
    # and it must refuse to be read as clearing the generator
    assert "does NOT clear the generator" in out


def test_it_names_the_earliest_component_in_generation_order(tmp_path) -> None:
    """Two arrays differ; the one reported must be the earlier GENERATED one,
    even though it is the alphabetically later of the pair."""

    base = {name: f"d_{name}" for name in _COMPONENTS}
    moved = dict(base)
    moved["user_velocities"] = "CHANGED"          # index 1 in generation order
    moved["cluster_pause_times"] = "CHANGED"      # last in generation order
    left = _artifact(tmp_path / "l.json", [_world("audit", 0, digests=base)])
    right = _artifact(tmp_path / "r.json",
                      [_world("audit", 0, digests=moved, fingerprint="other")])
    code, out = _run(left, right)
    assert code == 0
    assert "FIRST_DIVERGENCE:user_velocities" in out
    assert "earliest in generation order: user_velocities" in out


def test_a_differing_identity_is_refused_not_reported(tmp_path) -> None:
    """The paired negative for the refusal. Different seed -> the worlds are
    SUPPOSED to differ, so any divergence is uninformative."""

    base = {name: f"d_{name}" for name in _COMPONENTS}
    moved = dict(base, user_positions="CHANGED")
    left = _artifact(tmp_path / "l.json", [_world("audit", 0, digests=base, seed=7)])
    right = _artifact(tmp_path / "r.json",
                      [_world("audit", 0, digests=moved, seed=8)])
    code, out = _run(left, right)
    assert code == 1, "a mismatched identity must not produce a divergence verdict"
    assert "REFUSED" in out
    assert "user_world_seed" in out
    assert "FIRST_DIVERGENCE" not in out


def test_artifacts_without_component_digests_are_called_out(tmp_path) -> None:
    """H and run 30479940700 are in exactly this state; the script must say so
    rather than silently reporting 'identical'."""

    world = _world("audit", 0, digests={})
    del world["component_digests"]
    left = _artifact(tmp_path / "l.json", [world])
    right = _artifact(tmp_path / "r.json", [dict(world)])
    code, out = _run(left, right)
    assert "carry no component_digests" in out
    assert "WORLD_COMPONENTS_IDENTICAL" in out  # nothing comparable, nothing found


def test_no_shared_keys_is_a_failure_not_a_pass(tmp_path) -> None:
    base = {name: f"d_{name}" for name in _COMPONENTS}
    left = _artifact(tmp_path / "l.json", [_world("audit", 0, digests=base)])
    right = _artifact(tmp_path / "r.json", [_world("calibration", 5, digests=base)])
    code, out = _run(left, right)
    assert code == 1
    assert "NO_SHARED_EPISODE_KEYS" in out


def test_the_out_file_records_the_verdict(tmp_path) -> None:
    base = {name: f"d_{name}" for name in _COMPONENTS}
    moved = dict(base, user_waypoints="CHANGED")
    left = _artifact(tmp_path / "l.json", [_world("audit", 0, digests=base)])
    right = _artifact(tmp_path / "r.json",
                      [_world("audit", 0, digests=moved, fingerprint="other")])
    out_path = tmp_path / "verdict.json"
    code, _ = _run(left, right, out=str(out_path))
    assert code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["verdict"] == "FIRST_DIVERGENCE:user_waypoints"
    assert payload["comparable"] == 1
    assert payload["first_differing_tally"] == {"user_waypoints": 1}
