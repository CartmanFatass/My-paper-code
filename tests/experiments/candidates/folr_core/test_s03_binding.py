"""Proof-sized tests for the FOLR S03 binding registry and capture sink.

The load-bearing tests here are the two that protect the subsystem:
``test_installing_a_sink_does_not_change_the_action_path`` and
``test_no_sink_leaves_the_witness_fields_empty``.  The capture hook lives inside
``ha_ctse_process/`` and would be worthless -- worse, actively misleading -- if
it perturbed the run it is supposed to witness.

``test_direct_capture_agrees_with_replay`` is External Pro's witness layer C.
"""

from __future__ import annotations

import importlib.util
import pathlib

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core import s03_binding as sb

_HELPER_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "tests"
    / "process"
    / "variable_roster"
    / "ha_ctse_process_variable_roster_event_test.py"
)
_spec = importlib.util.spec_from_file_location("_folr_vre_helpers", _HELPER_PATH)
_helpers = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_helpers)

make_core = _helpers.make_core
initial_join = _helpers.initial_join

TARGET = "a"
SHADOW = "b"


def _binding(width: int = 10) -> sb.S03Binding:
    zero = np.zeros(width, dtype=np.float32)
    one = np.zeros(width, dtype=np.float32)
    one[0] = np.float32(1.5)
    neutral = np.full(width, np.float32(0.25))
    return sb.S03Binding.build(
        target_lifecycle_key=TARGET,
        target_membership_epoch=0,
        shadow_lifecycle_key=SHADOW,
        shadow_membership_epoch=0,
        h0=zero,
        h1=one,
        h_neutral=neutral,
    )


def _sink(core, binding: sb.S03Binding) -> sb.KernelCaptureSink:
    return sb.KernelCaptureSink(
        binding=binding,
        model_digest=sb.model_state_digest(core.commitment_model),
        snapshot_digest="test-snapshot",
    )


# --------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------


def test_registry_hashes_whole_vectors_not_the_differing_coordinate():
    """Pro: the registry must own and hash the ENTIRE vectors."""
    binding = _binding()
    baseline = binding.manifest_digest()

    # Change a coordinate that is NOT the one carrying the contrast.
    perturbed_h1 = binding.h1.copy()
    perturbed_h1[5] = np.float32(9.0)
    other = sb.S03Binding.build(
        target_lifecycle_key=TARGET,
        target_membership_epoch=0,
        shadow_lifecycle_key=SHADOW,
        shadow_membership_epoch=0,
        h0=binding.h0,
        h1=perturbed_h1,
        h_neutral=binding.h_neutral,
    )
    assert other.manifest_digest() != baseline, (
        "a complementary coordinate must move the manifest digest"
    )


def test_registry_refuses_an_empty_contrast():
    zero = np.zeros(10, dtype=np.float32)
    with pytest.raises(ValueError):
        sb.S03Binding.build(
            target_lifecycle_key=TARGET,
            target_membership_epoch=0,
            shadow_lifecycle_key=SHADOW,
            shadow_membership_epoch=0,
            h0=zero,
            h1=zero.copy(),
            h_neutral=zero.copy(),
        )


def test_registry_refuses_a_shadow_equal_to_the_target():
    with pytest.raises(ValueError):
        sb.S03Binding.build(
            target_lifecycle_key=TARGET,
            target_membership_epoch=0,
            shadow_lifecycle_key=TARGET,
            shadow_membership_epoch=0,
            h0=np.zeros(4, dtype=np.float32),
            h1=np.ones(4, dtype=np.float32),
            h_neutral=np.zeros(4, dtype=np.float32),
        )


def test_actor_preimage_digest_excludes_s03():
    """Including S03 would make the closure certificate vacuous."""
    base = {
        "observations": np.zeros((2, 3), dtype=np.float32),
        "architecture_mode": "f1",
        "pre_token_high_hidden": np.zeros(4, dtype=np.float32),
    }
    moved = dict(base)
    moved["pre_token_high_hidden"] = np.ones(4, dtype=np.float32)
    assert sb.actor_preimage_digest(base) == sb.actor_preimage_digest(moved)

    changed = dict(base)
    changed["observations"] = np.ones((2, 3), dtype=np.float32)
    assert sb.actor_preimage_digest(base) != sb.actor_preimage_digest(changed)


# --------------------------------------------------------------------------
# The subsystem hook
# --------------------------------------------------------------------------


def test_no_sink_leaves_the_witness_fields_empty():
    core = make_core()
    result = initial_join(core)
    assert result.token_rows
    for row in core.high_ledger:
        assert row.direct_masked_logits is None
        assert row.direct_probabilities is None
        assert row.actor_preimage_digest is None
        assert row.model_state_digest is None
        assert row.common_snapshot_digest is None
        assert row.intervention_manifest_digest is None


def test_installing_a_sink_does_not_change_the_action_path():
    """The witness must not perturb the run it witnesses."""
    plain = make_core()
    initial_join(plain)

    watched = make_core()
    watched.install_kernel_capture(_sink(watched, _binding(watched.high_hidden_dim)))
    initial_join(watched)

    assert len(plain.high_ledger) == len(watched.high_ledger)
    for left, right in zip(plain.high_ledger, watched.high_ledger):
        assert left.combined_action == right.combined_action
        assert left.sampled_order == right.sampled_order
        assert left.token_position == right.token_position
        assert left.sampled_replacement_gap == right.sampled_replacement_gap
        assert left.old_token_log_probability == right.old_token_log_probability
        assert np.array_equal(left.pre_token_high_hidden, right.pre_token_high_hidden)


def test_sink_captures_the_target_and_ignores_other_owners():
    core = make_core()
    binding = _binding(core.high_hidden_dim)
    sink = _sink(core, binding)
    core.install_kernel_capture(sink)
    initial_join(core, keys=(TARGET, SHADOW))

    assert len(sink.captures) == 1, "target_only must ignore the shadow owner"
    captured = sink.first()
    assert captured.owner_lifecycle_key == TARGET
    assert captured.membership_epoch == 0
    assert captured.probabilities.dtype == np.dtype(np.float32)
    assert captured.probabilities.shape == (core.n_skills,)
    assert captured.probabilities.sum() == pytest.approx(1.0, abs=1e-6)
    assert captured.intervention_manifest_digest == binding.manifest_digest()


def test_witness_fields_reach_the_immutable_row():
    core = make_core()
    binding = _binding(core.high_hidden_dim)
    core.install_kernel_capture(_sink(core, binding))
    initial_join(core, keys=(TARGET, SHADOW))

    target_rows = [
        row for row in core.high_ledger if row.owner_lifecycle_key == TARGET
    ]
    assert target_rows
    row = target_rows[0]
    assert row.direct_probabilities is not None
    assert row.direct_masked_logits is not None
    assert row.actor_preimage_digest
    assert row.model_state_digest
    assert row.intervention_manifest_digest == binding.manifest_digest()

    shadow_rows = [
        row for row in core.high_ledger if row.owner_lifecycle_key == SHADOW
    ]
    assert shadow_rows and shadow_rows[0].direct_probabilities is None


def test_direct_capture_agrees_with_replay():
    """Pro witness layer C: float64(direct float32) == replayed float64."""
    core = make_core()
    binding = _binding(core.high_hidden_dim)
    sink = _sink(core, binding)
    core.install_kernel_capture(sink)
    initial_join(core, keys=(TARGET, SHADOW))

    row = next(r for r in core.high_ledger if r.owner_lifecycle_key == TARGET)
    # `summary_source` is explicit and has no default -- exactly the ambiguity
    # Pro told us to record rather than assume.  At token position zero the
    # initial and working summaries coincide, so both must reproduce the direct
    # capture; asserting on both is what pins that claim instead of trusting it.
    assert row.token_position == 0
    direct = sink.first().probabilities
    for source in ("initial", "working"):
        replayed = np.asarray(
            core.replay_token_distribution(row, summary_source=source)
        )
        assert replayed.dtype == np.dtype(np.float64)
        assert np.array_equal(direct.astype(np.float64), replayed), source


def test_clearing_the_sink_restores_the_unwitnessed_path():
    core = make_core()
    core.install_kernel_capture(_sink(core, _binding(core.high_hidden_dim)))
    core.install_kernel_capture(None)
    initial_join(core)
    assert all(row.direct_probabilities is None for row in core.high_ledger)


def test_kernel_comparison_helpers():
    left = sb.DirectKernel(
        owner_lifecycle_key=TARGET,
        membership_epoch=0,
        token_position=0,
        masked_logits=np.zeros(3, dtype=np.float32),
        probabilities=np.asarray([0.5, 0.25, 0.25], dtype=np.float32),
        actor_preimage_digest="d",
        model_state_digest="m",
        common_snapshot_digest="s",
        intervention_manifest_digest="i",
    )
    same = sb.DirectKernel(**{**left.__dict__})
    assert sb.kernels_bitwise_equal(left, same)
    assert sb.kernel_infinity_norm(left, same) == 0.0

    moved = sb.DirectKernel(
        **{
            **left.__dict__,
            "probabilities": np.asarray([0.6, 0.2, 0.2], dtype=np.float32),
        }
    )
    assert not sb.kernels_bitwise_equal(left, moved)
    assert sb.kernel_infinity_norm(left, moved) == pytest.approx(0.1, abs=1e-6)
