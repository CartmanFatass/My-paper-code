"""V-K0A source-urgency oracle -- calibration of the exhaustive instrument.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D1,
VK-D10, A-VK-D2) and the two frozen rulings named there.

This machine's default pytest basetemp
(`C:\\Users\\fires\\AppData\\Local\\Temp\\pytest-of-fires`) is broken, so this
file never relies on the `tmp_path` fixture. Every scratch directory lives
under the repository's own `logs/_tmp_vk0a_oracle_test/` tree and is removed
after each test. Invoke with an explicit `--basetemp` anyway so pytest's own
collection-time temp directory (unrelated to these scratch dirs) does not
touch the broken default, e.g.:

    python -m pytest tests/audit_vk0a_oracle_test.py -q --basetemp logs/_pytest_basetemp
"""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "vk0a_oracle", PROJECT_ROOT / "scripts" / "audit_vk0a_source_urgency_oracle.py"
)
oracle = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = oracle
_SPEC.loader.exec_module(oracle)

import config_d7_2b_toy_learned_keep  # noqa: E402  (needs oracle's sys.path insert first)

SCRATCH_ROOT = PROJECT_ROOT / "logs" / "_tmp_vk0a_oracle_test"


def _fresh_scratch_dir(name: str) -> Path:
    d = SCRATCH_ROOT / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


@pytest.fixture(autouse=True)
def _clean_scratch():
    yield
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)


def _config():
    return config_d7_2b_toy_learned_keep.Config()


def test_end_to_end_panel_is_valid_and_deterministic():
    config = _config()

    artifact1 = oracle.build_panel(config)
    out1 = _fresh_scratch_dir("run1")
    panel1, sidecar1 = oracle.write_artifact(artifact1, out1)

    assert artifact1["row_count"] == 112
    assert len(artifact1["rows"]) == 112
    assert artifact1["verdict"] in (
        oracle.VALID_VERDICT,
        oracle.NOT_IDENTIFIED_VERDICT,
        oracle.INVALID_VERDICT,
    )
    assert artifact1["validity"]["all_passed"] is True
    for name in oracle.ValidityTracker.NAMES:
        assert artifact1["validity"][name] is True, name

    recomputed = hashlib.sha256(panel1.read_bytes()).hexdigest()
    assert sidecar1.read_text(encoding="utf-8").strip() == recomputed

    # Determinism: an independent second run must produce byte-identical
    # artifact bytes (no timestamps, no run-to-run float drift).
    artifact2 = oracle.build_panel(config)
    out2 = _fresh_scratch_dir("run2")
    panel2, _ = oracle.write_artifact(artifact2, out2)
    assert panel1.read_bytes() == panel2.read_bytes()


def test_permutation_relabel_matches_unordered_urgency_values():
    """A-VK-D2: at one sampled check, the two permutation tracks must expose
    the same *unordered* {U_src} value pair -- track choice only relabels
    which physical agent holds which duty, it must not change what the
    source contains."""
    config = _config()
    artifact = oracle.build_panel(config)
    rows = artifact["rows"]

    target_combo = rows[0]["sign_combo"]
    target_check = rows[0]["check_index"]
    by_track = {0: [], 1: []}
    for row in rows:
        if row["sign_combo"] == target_combo and row["check_index"] == target_check:
            by_track[row["assignment_permutation"]].append(row["U_src"])

    assert len(by_track[0]) == 2 and len(by_track[1]) == 2
    assert sorted(by_track[0]) == pytest.approx(sorted(by_track[1]), abs=1e-9)


def test_same_label_set_admission_flips_validity_to_invalid():
    """Paired negative for `same_label_set_excluded` (validity condition 4).

    Watched-fail ritual: corrupt the legality enumerator to admit a
    same-label SET, confirm the run goes red (validity fails, verdict is
    INVALID), restore, confirm green. A companion ad hoc check (reported
    alongside this test, not embedded here) additionally verified that with
    the guard predicates themselves stubbed out, the identical corruption is
    NOT caught -- proving this assertion exercises the guard rather than an
    incidental side effect.
    """
    config = _config()
    real_legal_options = oracle.legal_options

    def corrupted_legal_options(incumbent, n_skills=oracle.N_SKILLS):
        opts = real_legal_options(incumbent, n_skills)
        opts.append(("SET", int(incumbent)))  # illegal: same-label SET
        return opts

    oracle.legal_options = corrupted_legal_options
    try:
        artifact_red = oracle.build_panel(config)
    finally:
        oracle.legal_options = real_legal_options

    assert artifact_red["validity"]["same_label_set_excluded"] is False
    assert artifact_red["validity"]["legal_edit_enumeration_exact"] is False
    assert artifact_red["validity"]["all_passed"] is False
    assert artifact_red["verdict"] == oracle.INVALID_VERDICT

    # Revert and confirm green.
    artifact_green = oracle.build_panel(config)
    assert artifact_green["validity"]["all_passed"] is True
    assert artifact_green["verdict"] != oracle.INVALID_VERDICT
