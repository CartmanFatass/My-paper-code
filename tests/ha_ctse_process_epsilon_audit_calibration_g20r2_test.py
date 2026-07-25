"""Tests for the `epsilon_audit` fail-closed contract and its null calibration.

Covers design section 11's requirements: the module default must be
unreachable (`ha_ctse_process/anchor_action_advantage_g20r2.py`); the screen's
`run_identification_stages` must fail closed without a measured
`epsilon_audit_measurement` from THIS run
(`scripts/screen_anchor_action_advantage_g20r2.py`) -- the retired
`EPSILON_AUDIT_REGISTERED` registry and its lookup are gone entirely, not
just unused; the in-situ calibration must run at the exact fast anchor
snapshot with its own episode block verifiably disjoint from Stage A's audit
block (decision 1); the recorded measurement must carry the policy-snapshot
identity it was measured under (section 7); and the replicate-split null
calibration's own statistic (`scripts/calibrate_epsilon_audit_g20r2.py`) must
convert observed deltas to `epsilon_audit` correctly and must not silently
accept a degenerate self-vs-self measurement. No test here runs the
calibration at the full registered audit scale -- that is a bounded
diagnostic measurement executed separately, not a proof obligation of this
suite.
"""

from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process import anchor_action_advantage_g20r2 as credit_module
from scripts import screen_anchor_action_advantage_g20r2 as screen_module
from scripts import calibrate_epsilon_audit_g20r2 as calibration_module


# ---------------------------------------------------------------------------
# The unregistered default is unreachable.
# ---------------------------------------------------------------------------


def test_module_no_longer_exposes_an_epsilon_audit_default() -> None:
    assert not hasattr(credit_module, "EPSILON_AUDIT"), (
        "the silent EPSILON_AUDIT=1e-4 module default must be deleted, not "
        "merely unused, per design section 11"
    )


def test_stage_a_source_effect_requires_epsilon_audit_explicitly() -> None:
    generator = torch.Generator()
    generator.manual_seed(1)
    clusters = [torch.randn(4, 1, generator=generator) for _ in range(3)]
    with pytest.raises(TypeError):
        credit_module.stage_a_source_effect(clusters, generator=generator)  # type: ignore[call-arg]


def test_stage_a_source_effect_still_works_with_epsilon_audit_supplied() -> None:
    generator = torch.Generator()
    generator.manual_seed(2)
    clusters = [torch.randn(4, 1, generator=generator) for _ in range(3)]
    result = credit_module.stage_a_source_effect(
        clusters, generator=generator, epsilon_audit=1e-3
    )
    assert "passed" in result and "s_source_lcb95" in result


# ---------------------------------------------------------------------------
# The screen's `run_identification_stages` fails closed without a measured
# `epsilon_audit_measurement` from this run. The retired `EPSILON_AUDIT_
# REGISTERED` module-level registry and its `_registered_epsilon_audit`
# lookup are gone entirely (not merely unused): there is no longer a
# pre-registered-constant path for Stage A to fall back to.
# ---------------------------------------------------------------------------


def test_screen_no_longer_exposes_the_retired_epsilon_audit_registry() -> None:
    assert not hasattr(screen_module, "EPSILON_AUDIT_REGISTERED")
    assert not hasattr(screen_module, "_registered_epsilon_audit")


def _tiny_identification_clusters() -> dict[str, list[torch.Tensor]]:
    generator = torch.Generator()
    generator.manual_seed(4242)
    return {
        "oracle": [torch.randn(4, 1, generator=generator) for _ in range(6)],
        "critic": [torch.randn(4, 1, generator=generator) for _ in range(6)],
        "score": [torch.randn(4, 2, generator=generator) for _ in range(6)],
    }


def test_run_identification_stages_requires_epsilon_audit_measurement_explicitly() -> None:
    """Stage A must be structurally unreachable without a measured floor
    from this run -- exercised directly, not merely inferred from reading
    the signature."""

    clusters = _tiny_identification_clusters()
    with pytest.raises(TypeError):
        screen_module.run_identification_stages("g18", clusters, seed=1)  # type: ignore[call-arg]


def test_run_identification_stages_fails_closed_on_a_measurement_missing_epsilon_audit() -> None:
    """A measurement dict that forgot to carry its own `epsilon_audit` key
    (e.g. a caller that passed the wrong dict) must raise, not silently
    substitute a default."""

    clusters = _tiny_identification_clusters()
    with pytest.raises(KeyError):
        screen_module.run_identification_stages(
            "g18", clusters, seed=1, epsilon_audit_measurement={}
        )


def test_run_identification_stages_actually_gates_on_the_supplied_epsilon_audit() -> None:
    """The supplied value must reach Stage A's gate itself, not just get
    echoed back in the recorded metadata -- proven by flipping the pass/fail
    outcome with the floor alone, same clusters, same seed."""

    clusters = _tiny_identification_clusters()
    loose = screen_module.run_identification_stages(
        "g18", clusters, seed=1, epsilon_audit_measurement={"epsilon_audit": 1e-6}
    )
    strict = screen_module.run_identification_stages(
        "g18", clusters, seed=1, epsilon_audit_measurement={"epsilon_audit": 10.0}
    )
    assert loose["stage_a"]["epsilon_audit_squared"] == pytest.approx((1e-6) ** 2)
    assert strict["stage_a"]["epsilon_audit_squared"] == pytest.approx(100.0)
    assert loose["epsilon_audit_measurement"]["epsilon_audit"] == 1e-6
    assert strict["epsilon_audit_measurement"]["epsilon_audit"] == 10.0
    assert loose["stage_a_passed"] is True
    assert strict["stage_a_passed"] is False


# ---------------------------------------------------------------------------
# Policy-snapshot identity: a floor can never be silently paired with a
# different policy version than the one it was measured under (design
# sections 7 and 11).
# ---------------------------------------------------------------------------


def test_policy_snapshot_fingerprint_is_stable_at_fixed_weights_and_sensitive_to_drift() -> None:
    model = screen_module.make_model("g18")
    first = screen_module._policy_snapshot_fingerprint(model.anchor_state())
    second = screen_module._policy_snapshot_fingerprint(model.anchor_state())
    assert first == second, "the same weights must fingerprint identically"

    with torch.no_grad():
        model.log_std.add_(1e-3)
    drifted = screen_module._policy_snapshot_fingerprint(model.anchor_state())
    assert drifted != first, "even a small weight drift must change the fingerprint"


def test_require_matching_snapshot_passes_when_equal_and_raises_when_not() -> None:
    screen_module._require_matching_snapshot("abc", "abc", context="test")  # must not raise
    with pytest.raises(RuntimeError):
        screen_module._require_matching_snapshot("abc", "def", context="test")


# ---------------------------------------------------------------------------
# The in-situ path: `_measure_epsilon_audit` / `calibrate_source(model=...)`
# must reuse the caller's own trained model rather than silently rebuilding
# an untrained one (design section 11's decisive fourth condition), and its
# episode block must be verifiably disjoint from Stage A's own audit block
# (decision 1).
# ---------------------------------------------------------------------------


def test_calibrate_source_with_explicit_model_skips_configure_runtime_and_make_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The load-bearing wiring claim: supplying `model=` must reuse that
    exact object, never rebuild a fresh one. Proven by building the model
    with the real functions first, then breaking both rebuild paths and
    confirming they are never called."""

    model = calibration_module.make_model("g18")

    def _must_not_be_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("must not run when model= is provided explicitly")

    monkeypatch.setattr(calibration_module, "make_model", _must_not_be_called)
    monkeypatch.setattr(calibration_module.g17_runner, "configure_runtime", _must_not_be_called)

    result = calibration_module.calibrate_source(
        "g18",
        model=model,
        episode_id_offset=1_000,
        audit_episodes=2,
        points_per_episode=1,
        suffix_replicates=2,
        k=2,
    )
    assert result["episode_ids"] == [1_000, 1_001]


def test_measure_epsilon_audit_forwards_model_and_offset_to_calibrate_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`screen._measure_epsilon_audit` is the screen's own lazily-imported
    call site into the shared calibration -- prove it actually forwards the
    live model and offset rather than reconstructing its own."""

    captured: dict[str, object] = {}

    def _stub_calibrate_source(source: str, *, model: object, episode_id_offset: int) -> dict:
        captured["source"] = source
        captured["model"] = model
        captured["episode_id_offset"] = episode_id_offset
        return {"epsilon_audit": 0.5, "episode_ids": [episode_id_offset]}

    monkeypatch.setattr(calibration_module, "calibrate_source", _stub_calibrate_source)

    sentinel_model = object()
    result = screen_module._measure_epsilon_audit(
        "g18", sentinel_model, episode_id_offset=77_000
    )
    assert captured == {
        "source": "g18",
        "model": sentinel_model,
        "episode_id_offset": 77_000,
    }
    assert result["episode_ids"] == [77_000]


def test_calibration_and_audit_episode_blocks_are_disjoint_under_the_real_configuration() -> None:
    """Replicates `_train_source`'s own episode-block arithmetic for both
    registered sources at their configured phase-update counts and proves
    the calibration block never collides with Stage A's audit block --
    design section 11, decision 1, asserted in code rather than trusted from
    the offset constants alone."""

    for source, qualification_updates, fast_updates in (
        (
            "g17",
            screen_module.G17_QUALIFICATION_UPDATES,
            screen_module.G17_FAST_UPDATES,
        ),
        (
            "g18",
            screen_module.G18_QUALIFICATION_UPDATES,
            screen_module.G18_FAST_UPDATES,
        ),
    ):
        base = (fast_updates + qualification_updates) * screen_module.NUM_ENVS
        qualification_episode_ids = tuple(
            fast_updates * screen_module.NUM_ENVS + index
            for update in range(qualification_updates)
            for index in screen_module._qualification_episode_block(source, update)
        )
        audit_episode_ids = tuple(
            base + 10_000 + index for index in range(screen_module.AUDIT_EPISODES)
        )
        calibration_offset = base + 30_000
        calibration_episode_ids = tuple(
            calibration_offset + index
            for index in range(calibration_module.CALIBRATION_AUDIT_EPISODES)
        )
        credit_module.validate_disjoint_roles(
            qualification_episode_ids, calibration_episode_ids, audit_episode_ids
        )  # must not raise


def test_calibration_and_audit_episode_blocks_can_actually_be_caught_colliding() -> None:
    """Proves the guard above has teeth: a deliberately colliding
    calibration block must be rejected, not silently accepted -- otherwise
    the passing test above would be evidence of nothing."""

    audit_episode_ids = (10_000, 10_001, 10_002)
    colliding_calibration_ids = (10_001, 20_000)
    with pytest.raises(ValueError):
        credit_module.validate_disjoint_roles(
            [], colliding_calibration_ids, audit_episode_ids
        )


# ---------------------------------------------------------------------------
# The replicate-split statistic itself: `|d| / sqrt(2)` and its upper tail.
# ---------------------------------------------------------------------------


def _delta_row(d: float, episode_id: int = 0, point_index: int = 0) -> calibration_module.ProbePointDelta:
    return calibration_module.ProbePointDelta(
        source="g17",
        episode_id=episode_id,
        point_index=point_index,
        intervention_time=0,
        intervention_position=0,
        delta_set_a=d,
        delta_set_b=0.0,
        d=d,
        d_over_sqrt2=abs(d) / math.sqrt(2.0),
    )


def test_epsilon_audit_statistic_converts_d_to_sqrt2_scale() -> None:
    """A single, known `d` must survive the pooled quantile as `|d|/sqrt(2)`
    unchanged when it is the only observation in its tail -- this is the
    exact arithmetic design section 11 specifies, and an implementation that
    forgot the `sqrt(2)` conversion (or inverted it) would fail this."""

    rows_by_episode = {
        0: [_delta_row(1.0)],
        1: [_delta_row(1.0)],
    }
    result = calibration_module._epsilon_audit_from_deltas(rows_by_episode, seed=123)
    expected = 1.0 / math.sqrt(2.0)
    assert result["max_abs_d_over_sqrt2"] == pytest.approx(expected)
    assert result["min_abs_d_over_sqrt2"] == pytest.approx(expected)
    # every observation is identical, so both the point quantile and its
    # bootstrap upper bound must collapse to that same value
    assert result["epsilon_audit"] == pytest.approx(expected, rel=1e-6)


def test_epsilon_audit_tracks_an_outlier_cluster() -> None:
    """One cluster with a much larger `|d|` must move the registered upper
    tail upward -- a statistic that only looked at typical clusters (e.g. the
    median) would fail this, which is exactly the "driven by one outlier
    cluster" failure mode the brief asks to be able to see."""

    quiet = {index: [_delta_row(0.01, episode_id=index)] for index in range(6)}
    result_quiet = calibration_module._epsilon_audit_from_deltas(quiet, seed=1)

    with_outlier = dict(quiet)
    with_outlier[6] = [_delta_row(50.0, episode_id=6)]
    result_outlier = calibration_module._epsilon_audit_from_deltas(with_outlier, seed=1)

    assert result_outlier["epsilon_audit"] > result_quiet["epsilon_audit"]
    assert result_outlier["max_abs_d_over_sqrt2"] == pytest.approx(50.0 / math.sqrt(2.0))


def test_epsilon_audit_requires_at_least_two_clusters() -> None:
    with pytest.raises(ValueError):
        calibration_module._epsilon_audit_from_deltas({0: [_delta_row(1.0)]}, seed=1)


def test_assert_distinct_pair_rejects_a_degenerate_identical_pair() -> None:
    """The design records the naive null's exact failure mode: identical
    arms under common random numbers return exactly zero and would register
    a floor no source could fail. This guard -- called by `_probe_point_delta`
    right after drawing its fixed probe pair -- must refuse a degenerate pair
    rather than silently letting it flow into a (fake) zero-resolution
    measurement."""

    with pytest.raises(ValueError):
        calibration_module._assert_distinct_pair(
            torch.tensor([0.3]),
            torch.tensor([0.3]),
            source="g17",
            episode_id=0,
            point_index=0,
        )
    # a genuinely distinct pair must not raise -- otherwise the guard would
    # also reject every real, well-formed measurement
    calibration_module._assert_distinct_pair(
        torch.tensor([0.3]),
        torch.tensor([-0.1]),
        source="g17",
        episode_id=0,
        point_index=0,
    )


# ---------------------------------------------------------------------------
# One bounded end-to-end exercise at trivial (non-registrable) scale.
# ---------------------------------------------------------------------------


def test_calibrate_source_runs_end_to_end_at_trivial_scale_on_g18() -> None:
    """Exercises the full wiring -- seeding, ledger/env construction, the
    anchor-resample probe draw, the two disjoint replicate sets, and the
    pooled statistic -- against the real G18 source at a scale far below the
    registered audit scale, purely to prove the pipeline runs without error
    and does not collapse to the degenerate zero the design retires. G18's
    horizon (12) keeps this cheap; the resulting number is not a candidate
    for registration (design section 11: only the configured audit scale is)."""

    result = calibration_module.calibrate_source(
        "g18",
        audit_episodes=2,
        points_per_episode=1,
        suffix_replicates=2,
        k=2,
    )
    assert result["num_clusters"] == 2
    assert result["num_observations"] == 2
    assert math.isfinite(result["epsilon_audit"])
    assert result["epsilon_audit"] >= 0.0
    # a run that always measured exactly zero resolution would silently
    # reproduce the degenerate self-vs-self failure design section 11 warns
    # against -- at least one observed decision point must show nonzero
    # suffix-noise resolution under a stochastic environment.
    assert result["max_abs_d_over_sqrt2"] > 0.0


# ---------------------------------------------------------------------------
# Support fix: the calibration draws only from the C1 action support, and
# the calibration point count is raised well above the screen's own ~24
# (design section 11: "the number of calibration points ... must be raised
# well above the screen's own audit point count").
# ---------------------------------------------------------------------------


def test_calibration_audit_episodes_is_well_above_the_screens_own_count() -> None:
    """A regression that reverted `CALIBRATION_AUDIT_EPISODES` back down to
    the screen's own `AUDIT_EPISODES` (or anything close to it) fails here."""

    assert calibration_module.CALIBRATION_AUDIT_EPISODES > screen_module.AUDIT_EPISODES
    screen_total_points = (
        screen_module.AUDIT_EPISODES * screen_module.AUDIT_PROBE_POINTS_PER_EPISODE
    )
    calibration_total_points = (
        calibration_module.CALIBRATION_AUDIT_EPISODES
        * screen_module.AUDIT_PROBE_POINTS_PER_EPISODE
    )
    assert calibration_total_points >= 5 * screen_total_points


def test_calibrate_source_default_audit_episodes_matches_the_raised_constant() -> None:
    signature = inspect.signature(calibration_module.calibrate_source)
    assert (
        signature.parameters["audit_episodes"].default
        == calibration_module.CALIBRATION_AUDIT_EPISODES
    )


def test_probe_point_delta_never_intervenes_on_an_inactive_g18_position() -> None:
    """Direct regression at the level the calibration itself uses: every
    (time, position) the fixed `_audit_probe_points` draws for a real G18
    ledger must be active at that time. G18's rotation window (t in [6, 10))
    drops active_count from 4 to 2 out of capacity 6, so a sampler that
    ignored activity (the retired defect) would violate this quickly."""

    ledger = calibration_module._make_ledger("g18", 0)
    horizon, capacity, action_dim = calibration_module._source_geometry("g18")
    active_counts = screen_module._episode_active_counts(
        horizon=horizon,
        capacity=capacity,
        action_dim=action_dim,
        env_factory=calibration_module._env_factory("g18", ledger),
    )
    generator = np.random.default_rng(7)
    for _ in range(100):
        for time_index, position in screen_module._audit_probe_points(
            "g18", generator, active_counts
        ):
            assert position < active_counts[time_index]


def test_calibrate_source_at_raised_scale_reduces_exact_zero_fraction_relative_to_uniform_grid() -> None:
    """The concrete prediction design section 2 makes about the retired
    defect: restricting probes to the C1 action support must substantially
    reduce the fraction of exact-zero contrasts relative to drawing from the
    full, unrestricted (horizon, capacity) grid -- because an inactive
    intervention is a structural no-op (the environment forces its executed
    action to zero regardless of the probe), so `delta_set_a` is bit-exact
    zero there, while an active intervention generically is not.

    This reimplements only the retired grid-uniform point selection (not the
    rest of the pipeline) to measure what the old code would have drawn, and
    feeds both point sets through the same, unmodified `_probe_point_delta`
    used at every registered scale."""

    def uniform_grid_points(generator: np.random.Generator, horizon: int, capacity: int):
        return [
            (int(generator.integers(0, horizon)), int(generator.integers(0, capacity)))
            for _ in range(3)
        ]

    horizon, capacity, action_dim = calibration_module._source_geometry("g18")
    model = calibration_module.make_model("g18")

    def zero_fraction(use_active_support: bool) -> float:
        total = 0
        zero = 0
        for episode_id in range(6):
            ledger = calibration_module._make_ledger("g18", episode_id)
            point_generator = np.random.default_rng(
                np.random.SeedSequence(
                    [int(calibration_module.SEEDS["g18"]["audit"]), episode_id, 700]
                )
            )
            if use_active_support:
                active_counts = screen_module._episode_active_counts(
                    horizon=horizon,
                    capacity=capacity,
                    action_dim=action_dim,
                    env_factory=calibration_module._env_factory("g18", ledger),
                )
                points = screen_module._audit_probe_points(
                    "g18", point_generator, active_counts
                )
            else:
                points = uniform_grid_points(point_generator, horizon, capacity)
            for point_index, (intervention_time, intervention_position) in enumerate(points):
                row = calibration_module._probe_point_delta(
                    model,
                    "g18",
                    ledger,
                    episode_id=episode_id,
                    point_index=point_index,
                    intervention_time=intervention_time,
                    intervention_position=intervention_position,
                    k=2,
                    suffix_replicates=2,
                )
                total += 1
                if row.delta_set_a == 0.0:
                    zero += 1
        return zero / total

    uniform_zero_fraction = zero_fraction(use_active_support=False)
    restricted_zero_fraction = zero_fraction(use_active_support=True)

    assert uniform_zero_fraction > 0.0, (
        "fixture must actually exercise the inactive window under the "
        "unrestricted grid or this comparison proves nothing"
    )
    assert restricted_zero_fraction < uniform_zero_fraction
