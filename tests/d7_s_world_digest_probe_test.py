"""The cheap probe must record what makes a cross-machine comparison meaningful.

`scripts/d7_s_world_digest_probe.py` exists because getting cross-machine
component digests otherwise costs a full audit run -- over half an hour per arm,
twice in CI -- for data that takes seconds to produce. Construction only: no
stepping, no continuations, no estimand.

Two properties carry the weight, and one of them already failed once:

1. it records the BLAS identity, not just the numpy version. The first version
   used `np.__config__.get_info`, which numpy 1.26 removed, so it silently
   recorded an empty BLAS dict -- and an empty dict compares equal across two
   genuinely different numerical stacks, which is the "same environment" false
   conclusion the field exists to prevent;
2. it refuses the R4 population under the wrong seed namespace, same as the
   rejoin probe, for the same measured reason.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "_digest_probe", ROOT / "scripts" / "d7_s_world_digest_probe.py")
PROBE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PROBE)


def test_runtime_identity_records_the_blas_configuration() -> None:
    """The regression guard for the empty-dict bug."""

    identity = PROBE.runtime_identity()
    blas = identity["numpy_blas"]
    assert blas, "BLAS identity is empty; two different stacks would compare equal"
    assert blas.get("name"), "no BLAS library name recorded"
    config = blas.get("openblas_configuration") or ""
    assert config, "no openblas configuration string recorded"
    # DYNAMIC_ARCH is the whole reason the version is insufficient: one wheel
    # carries many CPU kernels and picks at runtime.
    assert "DYNAMIC_ARCH" in config


def test_runtime_identity_records_cpu_and_features() -> None:
    identity = PROBE.runtime_identity()
    assert identity["machine"]
    assert identity["numpy"]
    features = identity["cpu_features"]
    assert features.get("dispatch"), "no CPU dispatch feature list recorded"


def test_it_writes_the_same_shape_the_localizer_reads(tmp_path) -> None:
    """The probe's output must be readable by
    `d7_s_world_component_digest_diff.py` with no special case, or the two halves
    of step 1 do not compose."""

    import json
    out = tmp_path / "probe.json"
    argv = sys.argv
    sys.argv = ["probe", "--topologies", "20260725", "--episodes", "1",
                "--blocks", "audit",
                "--contract-id", audit.CONTRACT_ID, "--out", str(out)]
    try:
        assert PROBE.main() == 0
    finally:
        sys.argv = argv

    payload = json.loads(out.read_text(encoding="utf-8"))
    worlds = payload["episode_world_provenance"]["episode_worlds"]
    assert len(worlds) == 1
    entry = worlds[0]
    for field in ("block", "episode_index", "episode_seed", "user_world_seed",
                  "pinned_coordinate_hash", "n_users", "component_digests"):
        assert field in entry, field
    assert len(entry["component_digests"]) == len(audit.WORLD_COMPONENT_ORDER)


def test_the_r4_population_under_the_wrong_namespace_is_refused() -> None:
    argv = sys.argv
    sys.argv = ["probe", "--contract-id", audit.CONTRACT_ID]
    try:
        with pytest.raises(SystemExit) as excinfo:
            PROBE.main()
        assert "REFUSED" in str(excinfo.value)
    finally:
        sys.argv = argv
