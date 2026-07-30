"""The R4 probe must roll R4's seed namespace, and say which one it rolled.

WHAT WENT WRONG (2026-07-29). `d7_s_r4_rejoin_exposure_probe.py` derived its
episode, energy and user-world seeds without passing `contract_id`. Both
`_derived_seed` and `user_world_seed` default to the module `CONTRACT_ID`
(R3's namespace) while every R4 driver passes `R4_POPULATION_NAMESPACE`
explicitly. The probe therefore rolled R3-namespace episodes at R4 topology
coordinates and reported `R4_REJOIN_PROBE_FIRED` -- a verdict about episodes no
R4 artifact contains, which then propagated into an evidence note as
"the branch fires on the R4 population".

Every derived seed differed, so this was not a near miss. What made it
survivable-looking was that nothing printed the namespace and the seeds are
opaque integers either way.

These tests pin the two properties that would have caught it: the wrong
namespace is REFUSED rather than defaulted around, and the namespace actually
used is recorded in the artifact.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "_r4_probe", ROOT / "scripts" / "d7_s_r4_rejoin_exposure_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROBE = _load_probe()


def test_the_two_namespaces_are_actually_different() -> None:
    """The premise. If these ever became equal the guard below would be vacuous
    and would keep passing while enforcing nothing."""

    assert audit.CONTRACT_ID != audit.R4_POPULATION_NAMESPACE
    a = audit._derived_seed(topology_seed=20260739, block="audit", idx=0,
                            tag="episode_seed")
    b = audit._derived_seed(topology_seed=20260739, block="audit", idx=0,
                            tag="episode_seed", contract_id=audit.R4_POPULATION_NAMESPACE)
    assert a != b, "the namespace does not reach the derived seed at all"
    c = audit.user_world_seed(topology_seed=20260739, block="audit", episode_index=0)
    d = audit.user_world_seed(topology_seed=20260739, block="audit", episode_index=0,
                              contract_id=audit.R4_POPULATION_NAMESPACE)
    assert c != d


def test_r4_population_under_the_default_namespace_is_refused() -> None:
    """The paired negative: the exact call the original probe made."""

    with pytest.raises(SystemExit) as excinfo:
        PROBE.assert_namespace_matches_population(
            list(audit.TOPOLOGY_SEEDS_R4), audit.CONTRACT_ID)
    message = str(excinfo.value)
    assert audit.R4_POPULATION_NAMESPACE in message
    assert "different episodes" in message


def test_r4_population_under_r4_namespace_is_allowed() -> None:
    PROBE.assert_namespace_matches_population(
        list(audit.TOPOLOGY_SEEDS_R4), audit.R4_POPULATION_NAMESPACE)


def test_a_non_r4_topology_set_is_not_constrained() -> None:
    """The guard is about the R4 population specifically -- a development
    topology may legitimately be rolled in the module namespace."""

    PROBE.assert_namespace_matches_population([20260725], audit.CONTRACT_ID)


def test_the_probe_defaults_to_the_r4_namespace() -> None:
    """Refusing the wrong value is not enough if the default is the wrong value:
    every invocation would have to remember the flag."""

    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--contract-id", default=audit.R4_POPULATION_NAMESPACE)
    assert ap.parse_args([]).contract_id == audit.R4_POPULATION_NAMESPACE

    source = (ROOT / "scripts" / "d7_s_r4_rejoin_exposure_probe.py").read_text(
        encoding="utf-8")
    assert 'default=audit.R4_POPULATION_NAMESPACE' in source


def test_the_namespace_is_threaded_and_recorded() -> None:
    """A namespace that is chosen correctly but never written down leaves the
    next reader with the same unanswerable question."""

    source = (ROOT / "scripts" / "d7_s_r4_rejoin_exposure_probe.py").read_text(
        encoding="utf-8")
    # threaded into all three seed derivations, not just some of them
    assert source.count("contract_id=contract_id") == 3, (
        "every seed derivation must take the namespace; a partially threaded "
        "namespace mixes two populations inside one episode")
    assert '"contract_id": args.contract_id' in source, "not recorded in --out"
    assert "seed namespace" in source, "not printed"
