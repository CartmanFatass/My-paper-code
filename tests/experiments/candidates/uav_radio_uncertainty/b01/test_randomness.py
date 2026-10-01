"""Published-only synthetic address checks: 113,500 normal values total.

One finite schedule: 5 physical API blocks (1,250 values), 3 model API
blocks (84,000), one independent physical reference (250) and one model
reference (28,000). Invalid-input/version tests generate zero values.
The synthetic namespaces below keep these queries off production tapes.
"""

import numpy as np
import pytest

from experiments.candidates.uav_radio_uncertainty.b01 import contract as c, randomness as r

SYNTHETIC_PHYSICAL_NAMESPACE = 0x54535048
SYNTHETIC_MODEL_NAMESPACE = 0x54534D43
PHYSICAL_QUERY_SCHEDULE = ((c.FIXTURE_SEED, 0), (c.FIXTURE_SEED, 0), (c.FIXTURE_SEED, 1),
                           (c.FIXTURE_CONSTRUCTOR_SEEDS[0], 0), (c.FIXTURE_SEED, 0))
MODEL_QUERY_SCHEDULE = ((c.FIXTURE_SEED, 0), (c.FIXTURE_SEED, 0), (c.FIXTURE_SEED, 4))
PROPOSED_NORMAL_VALUES = 113500


def assert_rng_state_equal(left, right):
    assert left[0] == right[0] and left[2:] == right[2:]
    np.testing.assert_array_equal(left[1], right[1])


def test_exact_addressed_blocks_repeatability_freshness_namespaces_and_rng_isolation(monkeypatch):
    monkeypatch.setattr(c, 'PHYSICAL_NAMESPACE', SYNTHETIC_PHYSICAL_NAMESPACE)
    monkeypatch.setattr(c, 'MODEL_NAMESPACE', SYNTHETIC_MODEL_NAMESPACE)
    global_before = np.random.get_state()
    geometry_rng = np.random.RandomState(c.FIXTURE_SEED)
    geometry_before = geometry_rng.get_state()
    physical = [r.physical_normals(np.int64(world), np.int64(tick)) for world, tick in PHYSICAL_QUERY_SCHEDULE]
    model = [r.model_normals(world, tick) for world, tick in MODEL_QUERY_SCHEDULE]
    expected_physical = np.random.Generator(np.random.Philox(np.random.SeedSequence(
        [SYNTHETIC_PHYSICAL_NAMESPACE, c.PHYSICAL_ROOT, c.FIXTURE_SEED, 0]))).standard_normal((5,50), dtype=np.float64)
    expected_model = np.random.Generator(np.random.Philox(np.random.SeedSequence(
        [SYNTHETIC_MODEL_NAMESPACE, c.MODEL_ROOT, c.FIXTURE_SEED, 0]))).standard_normal((16,7,5,50), dtype=np.float64)
    assert_rng_state_equal(global_before, np.random.get_state())
    assert_rng_state_equal(geometry_before, geometry_rng.get_state())
    for value in physical:
        assert value.shape == (5,50) and value.dtype == np.float64 and value.flags.c_contiguous
    for value in model:
        assert value.shape == (16,7,5,50) and value.dtype == np.float64 and value.flags.c_contiguous
    np.testing.assert_array_equal(physical[0], expected_physical)
    np.testing.assert_array_equal(model[0], expected_model)
    np.testing.assert_array_equal(physical[0], physical[1])
    np.testing.assert_array_equal(physical[0], physical[4])
    np.testing.assert_array_equal(model[0], model[1])
    assert not np.array_equal(physical[0], physical[2]) and not np.array_equal(physical[0], physical[3])
    assert not np.array_equal(model[0], model[2])
    assert not np.array_equal(physical[0], model[0][0,0])
    assert not np.shares_memory(physical[0], physical[1]) and not np.shares_memory(model[0], model[1])
    physical[0].fill(123.)
    model[0].fill(123.)
    np.testing.assert_array_equal(physical[4], expected_physical)
    np.testing.assert_array_equal(model[1], expected_model)
    assert sum(value.size for value in physical+model) + expected_physical.size+expected_model.size == PROPOSED_NORMAL_VALUES


@pytest.mark.parametrize('world,tick', [(-1,0),(True,0),(1.,0),(0,-1),(0,False),(0,1.)])
def test_invalid_physical_identifiers_never_construct_a_generator(world, tick, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid input attempted a generator')
    monkeypatch.setattr(np.random, 'Generator', forbidden)
    with pytest.raises(ValueError):
        r.physical_normals(world,tick)


@pytest.mark.parametrize('world,tick', [(-1,0),(True,0),(1.,0),(0,-4),(0,True),(0,4.),(0,1),(0,6)])
def test_invalid_model_identifiers_or_report_clock_never_construct_a_generator(world,tick,monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid input attempted a generator')
    monkeypatch.setattr(np.random,'Generator',forbidden)
    with pytest.raises(ValueError):
        r.model_normals(world,tick)


def test_wrong_numpy_version_fails_before_generation(monkeypatch):
    monkeypatch.setattr(np,'__version__','not-the-bound-version')
    def forbidden(*args, **kwargs):
        raise AssertionError('wrong version attempted a generator')
    monkeypatch.setattr(np.random,'Generator',forbidden)
    with pytest.raises(RuntimeError,match='NumPy 1.26.3'):
        r.physical_normals(c.FIXTURE_SEED,0)
    with pytest.raises(RuntimeError,match='NumPy 1.26.3'):
        r.model_normals(c.FIXTURE_SEED,0)
