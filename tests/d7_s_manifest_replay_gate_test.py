"""The replay gate must be able to say PASS, and must be hard to say it to.

`scripts/d7_s_manifest_replay_gate.py` is the Route A acceptance gate ordered by
the Pro ruling of 2026-07-30. Its predecessor's failure is the one to guard
against: `d7_s_world_conformance_gate.py` compares independently GENERATED worlds
and cannot certify replay at all, while looking like a conformance gate.

THE SHAPE OF THESE TESTS. One test builds a PASS. Every other test takes that
exact input and removes ONE thing, and asserts the verdict stops being PASS. That
is the paired-negative discipline applied to a gate rather than to a function: a
gate whose PASS survives the removal of a condition never required it.
"""
from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

GATE = ROOT / "scripts" / "d7_s_manifest_replay_gate.py"
INTERPRETER = sys.executable

import d7_s_manifest_replay_gate as gate  # noqa: E402
import d7_s_manifest_replay_probe as probe  # noqa: E402


def _episode(**over):
    entry = {
        "topology_seed": 20260725,
        "block": "audit",
        "episode_index": 0,
        "episode_seed": 111,
        "user_world_seed": 222,
        "assertions": {name: True for name in probe.ASSERTIONS},
        "failure": None,
        "manifest_payload_hash": "p" * 64,
        "replaced_a_different_world": True,
        "episode_world_fingerprint": "w" * 64,
        "pre_step_state_fingerprint": "s" * 64,
        "derived_state_rebuilt": ["_reset_connection_baseline", "_update_channel_state",
                                  "_update_uav_connections", "_compute_routing_paths"],
        "horizon": {
            "event_found": True,
            "roll_power": {"steps_rolled": 500},
            "post_roll_world_digests": {"user_positions": "a" * 64,
                                        "user_velocities": "b" * 64},
            "event_conformance_digest": "c" * 64,
            "duty_map_at_te_digest": "d" * 64,
            "snapshot_state_hash": "e" * 64,
            "unit_stable_digest": "f" * 64,
            "unit_flex_digest": "g" * 64,
            "horizons_executed": {"stable": 139, "flex": 550},
        },
    }
    entry.update(over)
    return entry


def _probe(pid=1, **over):
    payload = {
        "kind": "d7_s_manifest_replay_probe",
        "schema_version": 2,
        "contract_id": "DEV",
        "topology_seed": 20260725,
        "coordinate_hash": "h" * 64,
        "block": "audit",
        "manifest_set_hash": "i" * 64,
        "manifest_episode_count": 1,
        "horizon_executed": True,
        "assertion_names": list(probe.ASSERTIONS),
        "episodes": [_episode()],
        "runtime_identity": {"cpu_model": "AMD EPYC 7763"},
        "job_identity": {"github_run_id": None, "hostname": "runner", "pid": pid},
    }
    payload.update(over)
    return payload


def _run(tmp_path, left, right):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(left), encoding="utf-8")
    b.write_text(json.dumps(right), encoding="utf-8")
    proc = subprocess.run([INTERPRETER, str(GATE), "--samples", str(a), str(b)],
                          capture_output=True, text=True, cwd=str(ROOT))
    return proc.stdout + proc.stderr, proc.returncode


def test_two_independent_identical_probes_pass(tmp_path) -> None:
    out, code = _run(tmp_path, _probe(pid=1), _probe(pid=2))
    assert "MANIFEST_REPLAY_PASS" in out, out
    assert code == 0


def test_identical_hardware_does_not_block_a_replay_pass(tmp_path) -> None:
    """The ruling's amendment, and it reverses a rule this project wrote itself.

    The generator gate is right to demand distinguishable hardware; carrying that
    across to replay would make a homogeneous fleet produce a permanent UNTESTED
    for a byte-replay mechanism -- an unfalsifiable gate that reads like caution.
    """

    same = {"cpu_model": "AMD EPYC 7763", "processor": "x86_64"}
    out, code = _run(tmp_path, _probe(pid=1, runtime_identity=same),
                     _probe(pid=2, runtime_identity=same))
    assert "MANIFEST_REPLAY_PASS" in out, out
    assert code == 0


def test_the_same_execution_reported_twice_is_untested(tmp_path) -> None:
    """PAIRED NEGATIVE for independence. Identical job identity means one run's
    artifact copied, and comparing a thing to itself always agrees."""

    out, code = _run(tmp_path, _probe(pid=7), _probe(pid=7))
    assert "MANIFEST_REPLAY_UNTESTED" in out, out
    assert "independence" in out
    assert code == 1


def test_a_skipped_horizon_is_untested_not_a_pass(tmp_path) -> None:
    """PAIRED NEGATIVE for assertion 8, and the ruling's stated reason for it:
    initial replay can pass while later RPGM trigonometric updates diverge."""

    left = _probe(pid=1, horizon_executed=False)
    out, code = _run(tmp_path, left, _probe(pid=2))
    assert "MANIFEST_REPLAY_UNTESTED" in out, out
    assert "a8_full_horizon_equality" in out
    assert code == 1


def test_a_manifest_that_changed_nothing_is_untested(tmp_path) -> None:
    """PAIRED NEGATIVE for the sneakiest pass. If applying the manifest replaced
    no component, the env already held that world and the read-back proved
    nothing about replay -- it agreed with a world that was already there."""

    left = _probe(pid=1)
    left["episodes"] = [_episode(replaced_a_different_world=False)]
    out, code = _run(tmp_path, left, _probe(pid=2))
    assert "MANIFEST_REPLAY_UNTESTED" in out, out
    assert "already there" in out
    assert code == 1


@pytest.mark.parametrize("assertion", gate.LOCAL_ASSERTIONS)
def test_every_local_assertion_can_fail_the_gate(tmp_path, assertion) -> None:
    """Seven paired negatives. An assertion the gate reads but never acts on is
    an assertion nobody has."""

    left = _probe(pid=1)
    entry = _episode()
    entry["assertions"] = dict(entry["assertions"])
    entry["assertions"][assertion] = False
    left["episodes"] = [entry]
    out, code = _run(tmp_path, left, _probe(pid=2))
    assert "MANIFEST_REPLAY_FAIL" in out, out
    assert assertion in out
    assert code == 1


@pytest.mark.parametrize("field", gate.EQUALITY_FIELDS)
def test_every_pre_step_equality_can_fail_the_gate(tmp_path, field) -> None:
    right = _probe(pid=2)
    right["episodes"] = [_episode(**{field: "z" * 64})]
    out, code = _run(tmp_path, _probe(pid=1), right)
    assert f"MANIFEST_REPLAY_FAIL:{field}" in out or field in out, out
    assert code == 1


def test_a_horizon_divergence_names_the_first_component_in_generation_order(tmp_path) -> None:
    """The divergence this gate exists to catch: agreement at t=0 and disagreement
    after the roll, because the RPGM update re-executed the trig."""

    right = _probe(pid=2)
    entry = _episode()
    entry["horizon"] = copy.deepcopy(entry["horizon"])
    entry["horizon"]["post_roll_world_digests"]["user_velocities"] = "z" * 64
    right["episodes"] = [entry]
    out, code = _run(tmp_path, _probe(pid=1), right)
    assert "MANIFEST_REPLAY_FAIL" in out, out
    assert "first differing component after the roll: user_velocities" in out
    assert code == 1


def test_a_unit_digest_divergence_fails(tmp_path) -> None:
    """Primary-G component series and branch-relevant quantities both live in the
    per-limb units, so this is the assertion-8 bullet that reaches the claim."""

    right = _probe(pid=2)
    entry = _episode()
    entry["horizon"] = copy.deepcopy(entry["horizon"])
    entry["horizon"]["unit_flex_digest"] = "z" * 64
    right["episodes"] = [entry]
    out, code = _run(tmp_path, _probe(pid=1), right)
    assert "MANIFEST_REPLAY_FAIL" in out, out
    assert "unit_flex_digest" in out
    assert code == 1


def test_a_different_manifest_set_is_untested_not_compared(tmp_path) -> None:
    """Two probes that replayed different bytes agree or disagree about nothing."""

    out, code = _run(tmp_path, _probe(pid=1), _probe(pid=2, manifest_set_hash="q" * 64))
    assert "MANIFEST_REPLAY_UNTESTED" in out, out
    assert "manifest_set_hash differs" in out
    assert code == 1


def test_a_generator_conformance_artifact_is_refused(tmp_path) -> None:
    """The two gates answer different questions and their artifacts must not be
    interchangeable -- that substitution is how a generator diagnostic would end
    up certifying replay."""

    a = tmp_path / "a.json"
    a.write_text(json.dumps({"episode_world_provenance": {"episode_worlds": []}}),
                 encoding="utf-8")
    b = tmp_path / "b.json"
    b.write_text(json.dumps(_probe()), encoding="utf-8")
    proc = subprocess.run([INTERPRETER, str(GATE), "--samples", str(a), str(b)],
                          capture_output=True, text=True, cwd=str(ROOT))
    assert "not a manifest-replay probe artifact" in (proc.stdout + proc.stderr)
    assert proc.returncode != 0


def test_there_is_no_allow_same_runtime_escape() -> None:
    """The ruling: "The existing --allow-same-runtime escape must never exist on
    the conclusion-bearing route." A gate with an escape hatch is a gate that gets
    escaped by whoever needs it green."""

    source = GATE.read_text(encoding="utf-8")
    assert "add_argument(\"--allow" not in source
    assert "allow_same_runtime" not in source


def test_the_probe_refuses_a_confirmatory_topology() -> None:
    """§4 holds the R4 population unselected AND uninspected. A probe run over an
    R4 seed would generate and read its worlds while looking like apparatus work."""

    import audit_d7_s_event_aligned as audit

    with pytest.raises(probe.ReplayProbeError) as excinfo:
        probe.refuse_confirmatory_topology(audit.TOPOLOGY_SEEDS_R4[0])
    assert "frozen R4 population" in str(excinfo.value)
    probe.refuse_confirmatory_topology(audit.TOPOLOGY_SEED_DEV)   # must not raise


def test_the_probe_names_all_eight_assertions() -> None:
    assert len(probe.ASSERTIONS) == 8
    assert probe.ASSERTIONS[-1] == "a8_full_horizon_equality"
    assert set(gate.LOCAL_ASSERTIONS) == set(probe.LOCAL_ASSERTIONS)
