"""`seed_controls_generation` witnesses seed APPLICATION, not reproducibility.

WHAT WENT WRONG (2026-07-29). The field's docstring said True means "rebuilding
this episode at the same pinned topology and the same `user_world_seed`
reproduces this fingerprint". What it computes is that the pinned hash is set and
that the applied seed equals the recorded seed -- a seed-application witness.

Measured falsification: topology 20260736 / calibration / episode 0, at
identical `pinned_coordinate_hash`, identical `user_world_seed`, identical
`n_users`, and `seed_controls_generation` True on every side, produced three
different fingerprints (local `d700a69e`, run 30403322062 `b5007214`, run
30479940700 `6307c329`). Both cloud runs reported
`all_seed_controlled = True` over 128/128 episodes while disagreeing about 3 of
8 topologies' worlds, with numpy and python hard-pinned.

These tests pin the properties that actually hold, so the stronger claim cannot
be restored by editing a comment. They deliberately do NOT assert
cross-machine reproducibility -- that is the property that was measured false.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402


class _World:
    """The caller-visible surface `episode_world_fingerprint` reads."""

    def __init__(self, *, applied, pinned, n_users=3, positions=None):
        self.user_world_seed_applied = applied
        self.pinned_coordinate_hash = pinned
        self.n_users = n_users
        self.user_positions = np.arange(n_users * 3, dtype=np.float64).reshape(n_users, 3) \
            if positions is None else np.asarray(positions, dtype=np.float64)


def test_seed_control_is_true_when_the_recorded_seed_is_the_applied_seed() -> None:
    out = audit.episode_world_fingerprint(_World(applied=99, pinned="abc"), seed_value=99)
    assert out["seed_controls_generation"] is True
    assert out["user_world_seed"] == 99
    assert out["pinned_coordinate_hash"] == "abc"


def test_seed_control_is_false_when_the_applied_seed_differs() -> None:
    """The paired negative for the property that IS claimed."""

    out = audit.episode_world_fingerprint(_World(applied=98, pinned="abc"), seed_value=99)
    assert out["seed_controls_generation"] is False


def test_seed_control_is_false_without_a_pinned_topology() -> None:
    out = audit.episode_world_fingerprint(_World(applied=99, pinned=None), seed_value=99)
    assert out["seed_controls_generation"] is False


def test_seed_control_does_not_inspect_the_world_at_all() -> None:
    """THE POINT. Two DIFFERENT worlds, same seed bookkeeping, both True.

    This is the defect stated as a test: the flag cannot distinguish the worlds
    whose reproduction it was documented to guarantee. If someone later makes it
    a reproducibility claim again, they have to make this test fail first.
    """

    a = audit.episode_world_fingerprint(
        _World(applied=99, pinned="abc", positions=[[0.0, 0.0, 0.0]], n_users=1),
        seed_value=99)
    b = audit.episode_world_fingerprint(
        _World(applied=99, pinned="abc", positions=[[1.0, 2.0, 3.0]], n_users=1),
        seed_value=99)
    assert a["fingerprint"] != b["fingerprint"], "different worlds must hash differently"
    assert a["seed_controls_generation"] is True
    assert b["seed_controls_generation"] is True, (
        "the flag is blind to the world -- which is exactly why it cannot carry a "
        "reproducibility claim")


def test_the_fingerprint_still_separates_worlds() -> None:
    """The job the fingerprint DOES do: proving which world an episode ran in.
    Withdrawing the reproduction claim must not weaken this."""

    base = _World(applied=1, pinned="p", n_users=4)
    same = audit.episode_world_fingerprint(base, seed_value=1)["fingerprint"]
    again = audit.episode_world_fingerprint(base, seed_value=1)["fingerprint"]
    assert same == again, "the same world must hash the same way"

    moved = _World(applied=1, pinned="p", n_users=4)
    moved.user_positions = moved.user_positions + 1e-9
    assert audit.episode_world_fingerprint(moved, seed_value=1)["fingerprint"] != same, (
        "a 1e-9 shift must change the hash; this sensitivity is why the value is "
        "not portable across machines")


def test_the_documentation_no_longer_claims_reproduction() -> None:
    """A comment is the only place the overclaim lived, so a comment is where the
    regression would reappear."""

    source = (ROOT / "scripts" / "audit_d7_s_event_aligned.py").read_text(encoding="utf-8")
    start = source.index("def episode_world_fingerprint")
    block = source[start:start + 4000]
    assert "reproduces this fingerprint" not in block, (
        "the withdrawn reproduction claim is back in the docstring")
    assert "IT DOES NOT MEAN THE FINGERPRINT IS REPRODUCIBLE" in block


def test_component_digests_cover_exactly_what_the_fingerprint_hashes() -> None:
    """The per-array digests must be derived from the same bytes as the combined
    hash, or they localize the wrong thing.

    Added because runs 30403322062 and 30479940700 disagreed about 3 of 8
    worlds and the artifact could not say which array moved.
    """

    out = audit.episode_world_fingerprint(
        _World(applied=1, pinned="p", n_users=4), seed_value=1)
    digests = out["component_digests"]
    # only the arrays actually present on the object appear
    assert set(digests) == {"user_positions"}
    assert all(len(v) == 64 for v in digests.values())


def test_a_component_digest_moves_when_its_array_moves() -> None:
    """The paired negative. A digest that cannot change localizes nothing."""

    a = _World(applied=1, pinned="p", n_users=2)
    b = _World(applied=1, pinned="p", n_users=2)
    b.user_positions = b.user_positions + 1.0

    da = audit.episode_world_fingerprint(a, seed_value=1)
    db = audit.episode_world_fingerprint(b, seed_value=1)
    assert da["component_digests"]["user_positions"] != db["component_digests"]["user_positions"]
    assert da["fingerprint"] != db["fingerprint"]


def test_an_untouched_component_digest_stays_put() -> None:
    """The half that makes localization useful: only the moved array's digest
    changes, so a diff of two artifacts points at one component."""

    class _Two(_World):
        def __init__(self, *, shift):
            super().__init__(applied=1, pinned="p", n_users=2)
            self.user_velocities = np.zeros((2, 3), dtype=np.float64)
            self.user_positions = self.user_positions + shift

    a = audit.episode_world_fingerprint(_Two(shift=0.0), seed_value=1)
    b = audit.episode_world_fingerprint(_Two(shift=1.0), seed_value=1)
    assert a["component_digests"]["user_positions"] != b["component_digests"]["user_positions"]
    assert a["component_digests"]["user_velocities"] == b["component_digests"]["user_velocities"], (
        "an untouched array's digest moved, so the localization is not per-array")


def test_the_fingerprint_bytes_are_pinned() -> None:
    """A golden digest over a fixed synthetic world.

    The fingerprint is recorded in every artifact, so its byte layout is a
    contract: change the order, the shape encoding or the name encoding and every
    prior artifact silently becomes incomparable. Adding `component_digests`
    refactored this loop, and the only reason that was safe is that the combined
    bytes stayed identical -- verified against a real R4 env
    (topology 20260736 / calibration / 0 -> `d700a69e...`, unchanged across the
    refactor). This pins it without needing a 5-second env build.
    """

    world = _World(applied=7, pinned="pin", n_users=3)
    world.user_velocities = np.full((3, 3), 0.5, dtype=np.float64)
    world.user_pause_times = np.arange(3, dtype=np.float64)
    out = audit.episode_world_fingerprint(world, seed_value=7)
    assert out["fingerprint"] == (
        "50652d9b112b16386631b3b9038e1c98af700c68dc7a4d22e93ce1a0b5aeafb4"
    ), ("the fingerprint byte layout moved; every existing artifact's world "
        "provenance just became incomparable")
