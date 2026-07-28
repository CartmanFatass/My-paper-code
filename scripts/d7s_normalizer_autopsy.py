"""D7.S normalizer autopsy -- a ZERO-NEW-DATA diagnostic of the stored R3
event-aligned audit artifact.

Governing spec (frozen, verbatim authority): External Pro's convergence
ruling on the D7.S PRIMARY_G_DEGENERATE result (task brief, quoted in full in
the dispatch that produced this file). The first formal D7.S audit
(`scripts/audit_d7_s_event_aligned.py`) returned PRIMARY_G_DEGENERATE:
neither limb established a positive normalizer B_m, so the materiality scale
is unidentified. This script does not re-run the environment, does not add
topologies or replicates, and does not decide R4. It re-analyzes the SCALAR
quantities the registered run already recorded, conditional on the
correctness of that run's own execution path (Modification 1) -- it is not a
second validation of the environment trajectories, so every quantity this
script reports is prefixed "artifact-derived" and nothing here is a new
source-level result.

REUSE, never reimplement (Modification 3's "never a second implementation"
principle applies to every quantity these functions already compute):
`hierarchical_bootstrap_events`, `hierarchical_bootstrap_quantity`,
`draw_shared_topology_indices` and `compute_t_m_bootstrap` are imported
directly from `scripts/audit_d7_s_event_aligned.py` and never re-derived
here. `BOOTSTRAP_ITERS`, `BOOTSTRAP_SEED` and `MATERIALITY_COEFFICIENT` are
the same registered constants the R3 run used.

Modification 2's sentinel is the fail-closed precondition on every other
section: no autopsy statistic is emitted unless the artifact's identity,
labeling and (at full iteration count) its own recorded bounds are all
independently reproduced first.

Modification 4/6: this script emits an EVIDENCE VECTOR (N1, N2, N3, N4, N5,
selection instability), never a single winning explanation, and it may only
NOMINATE R4 candidates as non-binding recommendations -- the freeze or
carrier retirement is a scientific disposition made elsewhere, at the next
review boundary, never by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import zlib
from pathlib import Path
from typing import Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AUDIT_MODULE_PATH = PROJECT_ROOT / "scripts" / "audit_d7_s_event_aligned.py"


def _load_audit_module():
    """Loads `scripts/audit_d7_s_event_aligned.py` by exact file path (the
    same `importlib.util` idiom `tests/audit_d7_s_event_aligned_test.py`
    already uses), so this script imports the REGISTERED module regardless
    of package/import-path ambiguity. That module is READ-ONLY input here --
    this file never edits it and never reimplements anything it exports."""
    spec = importlib.util.spec_from_file_location(
        "audit_d7_s_event_aligned", AUDIT_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = _load_audit_module()

# =============================================================================
# Frozen constants -- input identity and reproducibility knobs
# =============================================================================

# The exact, byte-frozen input artifact this script is built against. Computed
# once (2026-07-28) from the recorded pooled artifact and hardcoded here as
# the reference: a reproducibility sentinel that trusted its own live-computed
# hash instead of a frozen literal would prove nothing, because a corrupted or
# substituted input would recompute a "matching" hash of ITSELF every time.
ARTIFACT_RELATIVE_PATH = "logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json"
EXPECTED_ARTIFACT_SHA256 = (
    "b087e67cfb79900015ecec16d8c89ad81b495fc23369299401217578b0933514"
)

# Modification 2 condition 6's numerical tolerance. The registered run
# reproduces its own six bounds to better than 1e-12 (measured manually,
# task brief); this is a wide safety margin around that, not a loosening of
# it -- still eight orders of magnitude tighter than any quantity this
# autopsy reports.
BOUND_TOLERANCE = 1e-9

# --quick is development-only plumbing (task brief): it must never be
# mistaken for a real run, so it gets its OWN frozen, tiny iteration count,
# never a user-suppliable knob. The real path always uses the registered
# `audit.BOOTSTRAP_ITERS`/`audit.BOOTSTRAP_SEED` and nothing else.
QUICK_ITERS = 40

REQUIRED_TOPOLOGY_UNIT_KEYS = (
    "calibration_units_stable", "calibration_units_flex",
    "audit_units_stable", "audit_units_flex",
)

# Maps this script's internal quantity keys to (a) the exact artifact field
# each is read from -- the unit mapping the task brief's Project Manager
# independently verified against the recorded run -- and (b) the
# "artifact-derived" label Modification 1 requires on every emitted number.
QUANTITY_ARTIFACT_KEY = {
    "b_stable": "calibration_units_stable",
    "b_flex": "calibration_units_flex",
    "u_star_stable": "audit_units_stable",
    "u_star_flex": "audit_units_flex",
}
QUANTITY_LABEL = {
    "b_stable": "artifact-derived B_stable",
    "b_flex": "artifact-derived B_flex",
    "u_star_stable": "artifact-derived U*_stable",
    "u_star_flex": "artifact-derived U*_flex",
}
LIMB_QUANTITIES = {
    "stable": ("b_stable", "u_star_stable"),
    "flex": ("b_flex", "u_star_flex"),
}


# =============================================================================
# Section 0 -- Modification 2 sentinel: fail closed before anything else runs
# =============================================================================

class SentinelFailure(RuntimeError):
    """Raised when one or more of the six Modification-2 preconditions does
    not hold. Never caught and silently downgraded -- the whole point of a
    fail-closed sentinel is that a failure here stops the autopsy before any
    statistic is emitted."""


def check_artifact_hash(raw_bytes: bytes, *,
                         expected: str = EXPECTED_ARTIFACT_SHA256) -> tuple[bool, str]:
    """Condition 1: the input artifact's own bytes, unconditionally -- this
    is what makes every other check meaningful, since a substituted or
    corrupted artifact could otherwise carry a self-consistent-looking
    `contract_id`/`topology_seeds`/etc. while being the wrong file.

    `expected` defaults to the frozen production reference and exists as a
    parameter ONLY so the test suite can drive this condition in isolation
    against a small synthetic fixture (its own hash, not the real 631KB
    artifact's) without changing what `main()` ever actually checks against."""
    actual = hashlib.sha256(raw_bytes).hexdigest()
    ok = actual == expected
    detail = "matches frozen reference" if ok else (
        f"expected {expected}, got {actual}")
    return ok, detail


def check_contract_and_procedure(result: dict) -> tuple[bool, str]:
    """Condition 2: contract ID and procedure version, checked against the
    SAME registered constants the R3 run itself is bound by -- never a
    second literal that could silently drift from the source module's own
    frozen values."""
    contract_id = result.get("contract_id")
    procedure_version = result.get("procedure_version")
    ok = (contract_id == audit.CONTRACT_ID
          and procedure_version == audit.TOPOLOGY_PROCEDURE_VERSION)
    detail = (f"contract_id={contract_id!r} (expected {audit.CONTRACT_ID!r}), "
              f"procedure_version={procedure_version!r} "
              f"(expected {audit.TOPOLOGY_PROCEDURE_VERSION!r})")
    return ok, detail


def check_topology_seeds(result: dict) -> tuple[bool, str]:
    """Condition 3: the exact initial topology set 20260726-20260733, in the
    exact registered order -- never the 16-topology expansion union, and
    never a reordered or partial subset."""
    expected = list(audit.TOPOLOGY_SEEDS_INITIAL)
    actual = result.get("topology_seeds")
    ok = actual == expected
    detail = f"expected {expected}, got {actual}"
    return ok, detail


def check_smoke_false(result: dict) -> tuple[bool, str]:
    """Condition 4: smoke=False. A SMOKE_NOT_A_RESULT artifact carries no
    scientific reading at all; the autopsy must refuse it outright rather
    than analyze it as though it were the formal run."""
    smoke = result.get("smoke")
    ok = smoke is False
    return ok, f"smoke={smoke!r}"


def check_topology_units_shape(result: dict) -> tuple[bool, str]:
    """Condition 5: the four expected topology_units collections --
    `calibration_units_stable`, `calibration_units_flex`,
    `audit_units_stable`, `audit_units_flex` -- present as lists on every
    one of the registered topologies. Structural only (this does not touch
    the six bounds; condition 6 does)."""
    topology_units = result.get("topology_units")
    expected_n = len(audit.TOPOLOGY_SEEDS_INITIAL)
    if not isinstance(topology_units, list) or len(topology_units) != expected_n:
        got = len(topology_units) if isinstance(topology_units, list) else type(topology_units).__name__
        return False, f"expected {expected_n} topology_units entries, got {got}"
    missing: list[str] = []
    for i, unit in enumerate(topology_units):
        if not isinstance(unit, dict):
            missing.append(f"topology_units[{i}] is not a dict")
            continue
        for key in REQUIRED_TOPOLOGY_UNIT_KEYS:
            if not isinstance(unit.get(key), list):
                missing.append(f"topology_units[{i}].{key}")
    ok = not missing
    detail = "all four collections present on every topology" if ok else (
        f"missing/invalid: {missing}")
    return ok, detail


def check_bounds_reproduction(result: dict, *, iters: int, seed: int,
                               tol: float) -> tuple[bool, str, Optional[dict]]:
    """Condition 6: exact reproduction of all six registered R3 bounds, via
    the SAME `compute_t_m_bootstrap` the registered run used -- never a
    second implementation of the bootstrap. The artifact's own recorded
    `t_m_bootstrap` block is the reference (task brief: "the current
    artifact's recorded bounds are the reference values"), not a separate
    hardcoded literal, so this check stays correct even if this script is
    ever pointed at a different (equally frozen) artifact."""
    topology_units = result.get("topology_units")
    if not isinstance(topology_units, list) or not topology_units:
        return False, "no usable topology_units to recompute bounds from", None
    try:
        recomputed = audit.compute_t_m_bootstrap(
            b_stable_topology_units=[u["calibration_units_stable"] for u in topology_units],
            b_flex_topology_units=[u["calibration_units_flex"] for u in topology_units],
            u_star_stable_topology_units=[u["audit_units_stable"] for u in topology_units],
            u_star_flex_topology_units=[u["audit_units_flex"] for u in topology_units],
            n_topo=len(topology_units), iters=iters, seed=seed)
    except (KeyError, TypeError, ValueError) as exc:
        # Condition 6 must evaluate independently of every other condition
        # (never short-circuited), including when the structural check
        # (condition 5) would separately have caught the same malformed
        # input -- a crash here would silently prevent conditions 1-5 from
        # ever being reported at all.
        return False, f"could not recompute bounds from topology_units: {exc!r}", None
    # `compute_t_m_bootstrap` also returns the raw (iters, n_topo)
    # `shared_topology_indices` array (~80,000 ints at the registered
    # BOOTSTRAP_ITERS/n_topo=8) for its OWN caller's reuse -- never meant to
    # be persisted, exactly as the registered `assemble_audit_result` itself
    # strips it before embedding `t_m_bootstrap` in its own JSON output.
    # Dropped here so this script's JSON does not silently balloon with a
    # full resampling-index dump on every real run.
    recomputed = {k: v for k, v in recomputed.items() if k != "shared_topology_indices"}
    recorded = result.get("t_m_bootstrap", {})
    mismatches: dict[str, dict] = {}
    for key in ("b_stable_lcb", "b_flex_lcb", "t_stable_ucb", "t_stable_lcb",
                "t_flex_lcb", "t_flex_ucb"):
        rec = recorded.get(key)
        got = recomputed.get(key)
        if rec is None or got is None or not math.isfinite(rec) or not math.isfinite(got) \
                or abs(rec - got) > tol:
            mismatches[key] = {"recorded": rec, "recomputed": got}
    ok = not mismatches
    detail = "all six bounds reproduced within tolerance" if ok else (
        f"mismatches (tol={tol}): {mismatches}")
    return ok, detail, recomputed


def run_sentinel(result: dict, raw_bytes: bytes, *, iters: int, seed: int,
                  tol: float = BOUND_TOLERANCE,
                  enforce_bounds: bool = True,
                  expected_hash: str = EXPECTED_ARTIFACT_SHA256) -> dict:
    """Runs all six Modification-2 conditions, EACH driven independently
    (never short-circuited on the first failure), and raises
    `SentinelFailure` listing every failed condition if any did not hold.
    `enforce_bounds=False` is --quick's ONLY effect on the sentinel: at
    lowered iteration count, condition 6 cannot reproduce the registered
    bounds (that is expected, not a defect), so it is reported SKIPPED
    rather than evaluated -- it is never silently marked passing.
    `expected_hash` defaults to the frozen production reference; see
    `check_artifact_hash`'s docstring for why it is overridable at all."""
    checks: dict[str, dict] = {}
    ok1, d1 = check_artifact_hash(raw_bytes, expected=expected_hash)
    checks["artifact_hash"] = {"ok": ok1, "detail": d1}
    ok2, d2 = check_contract_and_procedure(result)
    checks["contract_and_procedure"] = {"ok": ok2, "detail": d2}
    ok3, d3 = check_topology_seeds(result)
    checks["topology_seeds"] = {"ok": ok3, "detail": d3}
    ok4, d4 = check_smoke_false(result)
    checks["smoke_false"] = {"ok": ok4, "detail": d4}
    ok5, d5 = check_topology_units_shape(result)
    checks["topology_units_shape"] = {"ok": ok5, "detail": d5}

    recomputed_bounds: Optional[dict] = None
    if enforce_bounds:
        ok6, d6, recomputed_bounds = check_bounds_reproduction(
            result, iters=iters, seed=seed, tol=tol)
        checks["bounds_reproduction"] = {"ok": ok6, "detail": d6}
    else:
        checks["bounds_reproduction"] = {
            "ok": None,
            "detail": "SKIPPED_QUICK_MODE: lowered iteration count cannot "
                       "reproduce the registered bounds by construction.",
        }

    failed = [name for name, c in checks.items() if c["ok"] is False]
    if failed:
        exc = SentinelFailure(
            f"D7.S normalizer autopsy sentinel failed closed on: {failed}. "
            f"Detail: { {name: checks[name]['detail'] for name in failed} }"
        )
        exc.failed = failed
        exc.checks = checks
        raise exc
    return {"checks": checks, "recomputed_t_m_bootstrap": recomputed_bounds}


# =============================================================================
# Section 1 -- shared small utilities (new code; none of this exists in the
# registered module, so none of it is a "second implementation" of anything)
# =============================================================================

def extract_quantity_units(result: dict, quantity: str) -> list[list[dict]]:
    key = QUANTITY_ARTIFACT_KEY[quantity]
    return [unit[key] for unit in result["topology_units"]]


def topology_seeds_of(result: dict) -> list[int]:
    return [int(unit["topology_seed"]) for unit in result["topology_units"]]


def per_topology_points(units: list[list[dict]]) -> list[Optional[float]]:
    """The eight per-topology TRUE point values (RNG-free true-argmax path,
    `compute_point=True`/`iters=0`) Section A requires -- exactly what
    `audit.topology_weighted_point_estimate` averages internally, captured
    here per-topology instead of only as the final mean, via the SAME
    `hierarchical_bootstrap_events` call it makes."""
    out: list[Optional[float]] = []
    for events in units:
        if not events:
            out.append(None)
            continue
        point = audit.hierarchical_bootstrap_events(
            events, iters=0, seed=0, compute_point=True)["point"]
        out.append(float(point))
    return out


def sign_counts(values: list[Optional[float]]) -> dict:
    finite = [v for v in values if v is not None and math.isfinite(v)]
    return {
        "positive": sum(1 for v in finite if v > 0),
        "negative": sum(1 for v in finite if v < 0),
        "zero": sum(1 for v in finite if v == 0),
        "n": len(finite),
    }


def _rankdata(values: list[float]) -> np.ndarray:
    """Average-tie ranks (standard `scipy.stats.rankdata` behaviour),
    self-contained so this diagnostic script carries no new dependency."""
    arr = np.asarray(values, dtype=float)
    order = np.argsort(arr, kind="mergesort")
    ranks = np.empty(len(arr), dtype=float)
    ranks[order] = np.arange(1, len(arr) + 1, dtype=float)
    unique_vals, inverse, counts = np.unique(arr, return_inverse=True, return_counts=True)
    sums = np.zeros(len(unique_vals), dtype=float)
    np.add.at(sums, inverse, ranks)
    avg = sums / counts
    return avg[inverse]


def pearson_r(x: list[float], y: list[float]) -> float:
    x_arr, y_arr = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x_arr.size < 2 or np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return float("nan")
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def spearman_r(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return float("nan")
    return pearson_r(list(_rankdata(x)), list(_rankdata(y)))


# =============================================================================
# Section 2 -- Section A: standalone distributions (Modification 3's shared
# outer topology stream, independent inner calibration/audit resampling)
# =============================================================================

def standalone_distribution(units: list[list[dict]], *,
                             shared_topology_indices: np.ndarray, seed: int) -> dict:
    """One of Section A's four standalone distributions. Uses
    `hierarchical_bootstrap_quantity` directly (not only through
    `compute_t_m_bootstrap`, which discards the UCB95 half of B_m and both
    bounds of standalone U*_m) with the SAME shared outer topology stream
    every other primary quantity in this run uses -- Modification 3's
    "shared resampling means the same topology indices are used across
    primary quantities," preserving cross-quantity topology covariance."""
    bootstrap = audit.hierarchical_bootstrap_quantity(
        units, shared_topology_indices=shared_topology_indices, seed=seed)
    topo_points = per_topology_points(units)
    finite_points = [v for v in topo_points if v is not None and math.isfinite(v)]
    point = float(np.mean(finite_points)) if finite_points else float("nan")
    return {
        "point": point,
        "interval_5_95": [bootstrap["lo"], bootstrap["hi"]],
        "per_topology_points": topo_points,
        "min": min(finite_points) if finite_points else None,
        "max": max(finite_points) if finite_points else None,
        "sign_counts": sign_counts(topo_points),
    }


def leave_one_topology_out(units: list[list[dict]], *, iters: int, seed: int) -> list[dict]:
    """Section A's required leave-one-topology-out point AND interval
    sensitivity: with only eight top-level topologies, one topology can have
    substantial leverage. Each exclusion redraws the outer topology stream
    at n_topo=7 via the SAME registered `draw_shared_topology_indices`
    (never a hand-rolled resample), over the reduced seven-topology
    population."""
    out = []
    n_topo = len(units)
    for excluded in range(n_topo):
        reduced = [u for i, u in enumerate(units) if i != excluded]
        shared = audit.draw_shared_topology_indices(
            n_topo=len(reduced), iters=iters, seed=seed)
        bootstrap = audit.hierarchical_bootstrap_quantity(
            reduced, shared_topology_indices=shared, seed=seed)
        topo_points = [v for v in per_topology_points(reduced)
                       if v is not None and math.isfinite(v)]
        point = float(np.mean(topo_points)) if topo_points else float("nan")
        out.append({
            "excluded_topology_index": excluded,
            "point": point,
            "interval_5_95": [bootstrap["lo"], bootstrap["hi"]],
        })
    return out


# =============================================================================
# Section 3 -- N4: topology heterogeneity (s^2_between vs mean within-topology)
# =============================================================================

def within_topology_variance(units: list[list[dict]], *, iters: int, seed: int) -> list[Optional[float]]:
    """Modification E's "estimated average within-topology uncertainty
    derived by independently resampling events inside each topology": holds
    the topology fixed (a degenerate shared_topology_indices column that
    always selects that one topology slot) and reuses the SAME
    `hierarchical_bootstrap_quantity` nested-resampling machinery -- never a
    second bootstrap implementation -- restricted to one topology's own
    events, so the resulting variance is purely within-topology sampling
    variance."""
    out: list[Optional[float]] = []
    for t, events in enumerate(units):
        if not events:
            out.append(None)
            continue
        fixed_indices = np.full((int(iters), 1), t, dtype=np.int64)
        bootstrap = audit.hierarchical_bootstrap_quantity(
            units, shared_topology_indices=fixed_indices, seed=seed)
        finite = bootstrap["u_star_iters"][np.isfinite(bootstrap["u_star_iters"])]
        out.append(float(np.var(finite)) if finite.size else None)
    return out


def topology_heterogeneity_ratio(topo_points: list[Optional[float]],
                                  within_vars: list[Optional[float]]) -> dict:
    """Modification E's descriptive ratio: R_topology = max(0, s2_between -
    mean_s2_within) / (max(0, s2_between - mean_s2_within) + mean_s2_within).
    Descriptive only -- it "may raise TOPOLOGY_HETEROGENEITY_DOMINANT" and
    "does not establish a regime" (Modification 5)."""
    finite_points = [v for v in topo_points if v is not None and math.isfinite(v)]
    finite_within = [v for v in within_vars if v is not None and math.isfinite(v)]
    s2_between = float(np.var(finite_points)) if len(finite_points) >= 2 else float("nan")
    mean_s2_within = float(np.mean(finite_within)) if finite_within else float("nan")
    if not (math.isfinite(s2_between) and math.isfinite(mean_s2_within)):
        return {"s2_between": s2_between, "mean_s2_within": mean_s2_within, "r_topology": float("nan")}
    adjusted = max(0.0, s2_between - mean_s2_within)
    denom = adjusted + mean_s2_within
    r_topology = (adjusted / denom) if denom > 0 else 0.0
    return {"s2_between": s2_between, "mean_s2_within": mean_s2_within, "r_topology": r_topology}


def classify_n4(ratios: dict[str, dict]) -> tuple[str, str]:
    """Evidence-matrix mapping for N4 (dominant / material / not established)
    -- an interpretive threshold on the descriptive R_topology ratio's own
    natural [0, 1] scale, taken as the MAXIMUM across all four primary
    quantities: R_topology > 0.5 means the between-topology-adjusted signal
    exceeds the average within-topology noise floor for at least one
    quantity ("dominant"); 0 < R > 0.5 is "material"; R == 0 for every
    quantity means no quantity's between-topology spread exceeds its own
    within-topology sampling noise ("not established"). This threshold is
    this script's own interpretive choice (documented in the implementer
    report), not a value Modification 5 states numerically -- it decides
    only this diagnostic label, never a registered R3 branch."""
    values = [r["r_topology"] for r in ratios.values() if math.isfinite(r["r_topology"])]
    if not values:
        return "not established", "R_topology undefined for every quantity."
    worst = max(values)
    if worst > 0.5:
        return "dominant", f"max R_topology={worst:.4f} exceeds 0.5 for at least one quantity."
    if worst > 0.0:
        return "material", f"max R_topology={worst:.4f} is nonzero but does not exceed 0.5."
    return "not established", "R_topology is zero for every quantity."


# =============================================================================
# Section 4 -- N5: normalizer-relevance / comparator-mismatch association
# =============================================================================

def _topology_slot_resample_mean(events: list[dict], *, seed_tag: str, seed: int,
                                  i: int, slot: int) -> float:
    """One INDEPENDENT within-topology resample of one primary quantity's
    events for one (iteration, slot) pair, reusing
    `hierarchical_bootstrap_events` exactly as `hierarchical_bootstrap_
    quantity` does internally. `seed_tag` ("assoc_b" vs "assoc_u")
    deliberately disambiguates the calibration (B_m) and audit (U*_m) draws
    beyond the incidental fact that their event counts usually differ --
    Modification 3 requires the calibration and audit blocks be resampled
    independently within a topology, and this makes that independence
    explicit rather than accidental."""
    if not events:
        return float("nan")
    # `default_rng`'s SeedSequence accepts only ints (or sequences of ints),
    # never a string -- the tag is folded to a stable small int via CRC32 so
    # the two tags stay a pure, reproducible function of their literal text.
    tag_int = int(zlib.crc32(seed_tag.encode("utf-8")))
    ev_rng = np.random.default_rng((int(seed), int(i), int(slot), tag_int))
    idx = ev_rng.integers(0, len(events), size=len(events))
    resampled = [events[j] for j in idx]
    inner_seed = int(ev_rng.integers(0, 2 ** 63 - 1))
    inner = audit.hierarchical_bootstrap_events(
        resampled, iters=1, seed=inner_seed, compute_point=False)
    return float(inner["u_star_iters"][0])


def bootstrap_association(b_units: list[list[dict]], u_units: list[list[dict]], *,
                           shared_topology_indices: np.ndarray, seed: int) -> dict:
    """Modification F items 3-4: resample TOPOLOGIES jointly (the SAME
    `shared_topology_indices` column per iteration drives both quantities),
    but resample the calibration (B_m) and audit (U*_m) observations
    INDEPENDENTLY within each drawn topology. Produces a bootstrap
    distribution of the Pearson and rank association between the two
    quantities' per-topology-slot values."""
    iters, n_topo = shared_topology_indices.shape
    pearson_iters = np.full(iters, np.nan)
    rank_iters = np.full(iters, np.nan)
    for i in range(iters):
        topo_idx = shared_topology_indices[i]
        b_vals, u_vals = [], []
        for slot, ti in enumerate(topo_idx):
            ti = int(ti)
            bm = _topology_slot_resample_mean(
                b_units[ti], seed_tag="assoc_b", seed=seed, i=i, slot=slot)
            um = _topology_slot_resample_mean(
                u_units[ti], seed_tag="assoc_u", seed=seed, i=i, slot=slot)
            if math.isfinite(bm) and math.isfinite(um):
                b_vals.append(bm)
                u_vals.append(um)
        if len(b_vals) >= 2:
            pearson_iters[i] = pearson_r(b_vals, u_vals)
            rank_iters[i] = spearman_r(b_vals, u_vals)
    finite_p = pearson_iters[np.isfinite(pearson_iters)]
    finite_r = rank_iters[np.isfinite(rank_iters)]
    return {
        "pearson_interval_5_95": (
            [float(np.percentile(finite_p, 5)), float(np.percentile(finite_p, 95))]
            if finite_p.size else [None, None]),
        "rank_interval_5_95": (
            [float(np.percentile(finite_r, 5)), float(np.percentile(finite_r, 95))]
            if finite_r.size else [None, None]),
    }


def loto_association(b_topo_points: list[Optional[float]],
                      u_topo_points: list[Optional[float]]) -> list[dict]:
    """Modification F item 5: leave-one-topology-out association, over the
    already-computed TRUE per-topology points (RNG-free, no bootstrap
    needed)."""
    n = len(b_topo_points)
    out = []
    for excluded in range(n):
        bx = [b_topo_points[i] for i in range(n) if i != excluded]
        ux = [u_topo_points[i] for i in range(n) if i != excluded]
        pairs = [(b, u) for b, u in zip(bx, ux)
                 if b is not None and u is not None and math.isfinite(b) and math.isfinite(u)]
        if len(pairs) >= 2:
            bx2, ux2 = zip(*pairs)
            pearson = pearson_r(list(bx2), list(ux2))
            rank = spearman_r(list(bx2), list(ux2))
        else:
            pearson = rank = float("nan")
        out.append({"excluded_topology_index": excluded, "pearson": pearson, "rank": rank})
    return out


def classify_n5(pearson_point: float, rank_point: float, pearson_interval: list) -> tuple[str, str]:
    """Modification F: "a weak, unstable, or negative relation raises N5; it
    does not prove it." Interpretive thresholds (documented, this script's
    own choice, not stated numerically in the ruling): |r| >= 0.5 AND the
    bootstrap interval excludes zero on the SAME sign as the point ->
    "lowered" (a clean positive/negative correlation argues the normalizer
    tracks the focal effect, i.e. against comparator mismatch being the
    story). Anything weak, unstable (interval straddles zero) or negative ->
    "raised". A moderate but unstable positive relation -> "compatible"."""
    lo, hi = pearson_interval
    if lo is None or hi is None or not (math.isfinite(pearson_point) and math.isfinite(rank_point)):
        return "raised", "association undefined (degenerate variance in one or both quantities)."
    stable_nonzero = (lo > 0) or (hi < 0)
    if pearson_point < 0 or rank_point < 0:
        return "raised", f"pearson={pearson_point:.3f} rank={rank_point:.3f}: negative relation."
    if abs(pearson_point) < 0.3 or not stable_nonzero:
        return "raised", f"pearson={pearson_point:.3f} rank={rank_point:.3f}, interval [{lo:.3f}, {hi:.3f}]: weak or unstable."
    if abs(pearson_point) >= 0.5 and stable_nonzero:
        return "lowered", f"pearson={pearson_point:.3f} rank={rank_point:.3f}, interval [{lo:.3f}, {hi:.3f}]: stable positive relation."
    return "compatible", f"pearson={pearson_point:.3f} rank={rank_point:.3f}, interval [{lo:.3f}, {hi:.3f}]: moderate."


# =============================================================================
# Section 5 -- N1 evidence hierarchy (Modification B, frozen before looking
# at the output)
# =============================================================================

def classify_n1(*, b_topo_points: list[Optional[float]],
                 u_topo_points: list[Optional[float]],
                 u_interval: list[float],
                 u_loto_points: list[float]) -> tuple[str, str]:
    """Modification B's three-tier hierarchy, translated to code exactly as
    stated:

    Strong -- B_m has both positive and negative topology values, while the
    standalone pooled U*_m interval excludes zero and its LOTO direction
    does not reverse -> "raised".

    Moderate -- B_m crosses zero, while most topology-level U*_m values
    share one sign but the pooled interval still includes zero ->
    "compatible".

    No resolved -- both B_m and U*_m change direction materially (B_m
    crosses zero and U*_m's topology-level signs are not majority-one-sign)
    -> "compatible" (undiscriminated by this pattern, not evidence against).

    A fourth pattern the ruling does not name explicitly but that Strong/
    Moderate/No-resolved jointly presuppose: if B_m does NOT cross zero at
    all (every topology value shares one sign), the "signed-normalizer
    failure" premise itself is not observed in this artifact -> "lowered".
    This fourth-branch mapping is this script's own interpretive extension
    (documented in the implementer report), not literal ruling text."""
    b_finite = [v for v in b_topo_points if v is not None and math.isfinite(v)]
    u_finite = [v for v in u_topo_points if v is not None and math.isfinite(v)]
    b_crosses = any(v > 0 for v in b_finite) and any(v < 0 for v in b_finite)
    if not b_crosses:
        return "lowered", "B_m does not cross zero across topologies; signed-normalizer-failure premise not observed."

    lo, hi = u_interval
    u_resolved = (lo > 0) or (hi < 0)
    if u_resolved:
        u_sign = 1 if lo > 0 else -1
        loto_signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in u_loto_points if math.isfinite(v)]
        loto_stable = all(s != -u_sign for s in loto_signs)
        if loto_stable:
            return "raised", ("B_m crosses zero across topologies; standalone U*_m interval excludes "
                               "zero and its leave-one-topology-out direction does not reverse.")

    pos = sum(1 for v in u_finite if v > 0)
    neg = sum(1 for v in u_finite if v < 0)
    majority_one_sign = u_finite and max(pos, neg) > len(u_finite) / 2.0
    if majority_one_sign and not u_resolved:
        return "compatible", ("B_m crosses zero; most topology-level U*_m values share one sign, "
                               "but the pooled U*_m interval still includes zero (moderate).")
    return "compatible", "both B_m and U*_m change direction materially across topologies; not resolved by this pattern."


# =============================================================================
# Section 6 -- N2 (Modification C)
# =============================================================================

def classify_n2(u_stable_interval: list[float], u_flex_interval: list[float]) -> tuple[str, str]:
    """Modification C: U*_stable positively resolved supports "best focal
    SET beats KEEP on the stable class"; U*_flex negatively resolved
    supports "focal renewal worse than KEEP on the flex class". These are
    the two legs of one "opposite source direction" pattern -- "resolved"
    requires BOTH legs; one leg alone is "compatible" (partial); neither is
    "not resolved". This two-leg AND-requirement for "resolved" is this
    script's interpretive reading of "opposite... direction" (documented in
    the implementer report), not literal ruling text."""
    stable_lo, stable_hi = u_stable_interval
    flex_lo, flex_hi = u_flex_interval
    stable_resolved = stable_lo > 0
    flex_resolved = flex_hi < 0
    if stable_resolved and flex_resolved:
        return "resolved", "U*_stable positively resolved and U*_flex negatively resolved."
    if stable_resolved or flex_resolved:
        leg = "U*_stable positively resolved" if stable_resolved else "U*_flex negatively resolved"
        return "compatible", f"only one leg resolved ({leg})."
    return "not resolved", "neither U*_stable nor U*_flex is resolved in the direction N2 requires."


# =============================================================================
# Section 7 -- selection-instability diagnostic (Modification G), read from
# the artifact's OWN already-recorded `selection_diagnostic` block -- no new
# bootstrap, purely descriptive aggregation of stored data
# =============================================================================

def selection_instability_summary(result: dict, topo_points: dict[str, list]) -> dict:
    out: dict[str, dict] = {}
    for limb in ("stable", "flex"):
        entries = result.get("selection_diagnostic", {}).get(limb, [])
        entropies = [e["normalized_entropy"] for e in entries if e.get("normalized_entropy") is not None]
        leading_freqs = [
            max(e["selection_frequency"].values()) if e.get("selection_frequency") else None
            for e in entries
        ]
        leading_freqs = [f for f in leading_freqs if f is not None]
        n = len(entries)
        below_60 = sum(1 for f in leading_freqs if f < 0.60)
        below_75 = sum(1 for f in leading_freqs if f < 0.75)

        u_key = "u_star_stable" if limb == "stable" else "u_star_flex"
        abs_u_by_topology = [abs(v) if v is not None and math.isfinite(v) else None
                              for v in topo_points[u_key]]
        entropy_series, abs_u_series = [], []
        for e in entries:
            ti = e.get("topology_index")
            if ti is None or ti >= len(abs_u_by_topology):
                continue
            u_val = abs_u_by_topology[ti]
            ent = e.get("normalized_entropy")
            if u_val is not None and ent is not None:
                entropy_series.append(ent)
                abs_u_series.append(u_val)
        association = pearson_r(entropy_series, abs_u_series) if len(entropy_series) >= 2 else float("nan")

        out[limb] = {
            "n_events": n,
            "median_normalized_entropy": float(np.median(entropies)) if entropies else None,
            "range_normalized_entropy": [float(min(entropies)), float(max(entropies))] if entropies else None,
            "fraction_leading_below_0_60": (below_60 / n) if n else None,
            "fraction_leading_below_0_75": (below_75 / n) if n else None,
            "association_entropy_vs_abs_u_star_topology_point": association,
        }
    return out


def classify_selection_instability(summary: dict) -> tuple[str, str]:
    """high / moderate / low, taken as the worst across limbs. Interpretive
    thresholds (this script's own choice, documented): high if a majority of
    events have leading-candidate frequency below 0.60 in either limb;
    moderate if a majority are below 0.75 but not below 0.60; low
    otherwise."""
    worst = "low"
    detail_parts = []
    for limb, s in summary.items():
        f60 = s["fraction_leading_below_0_60"]
        f75 = s["fraction_leading_below_0_75"]
        if f60 is None:
            continue
        if f60 > 0.5:
            level = "high"
        elif f75 is not None and f75 > 0.5:
            level = "moderate"
        else:
            level = "low"
        detail_parts.append(f"{limb}: frac<0.60={f60:.2f} frac<0.75={f75:.2f} -> {level}")
        if {"low": 0, "moderate": 1, "high": 2}[level] > {"low": 0, "moderate": 1, "high": 2}[worst]:
            worst = level
    return worst, "; ".join(detail_parts) if detail_parts else "no selection-diagnostic data."


# =============================================================================
# Section 8 -- assembly, output, CLI
# =============================================================================

N3_STATEMENT = ("Primary-G component cancellation remains compatible with every scalar "
                "pattern observed in this autopsy.")


def run_autopsy(*, artifact_path: Path, iters: int, seed: int, quick: bool) -> dict:
    raw_bytes = artifact_path.read_bytes()
    result = json.loads(raw_bytes)

    sentinel = run_sentinel(result, raw_bytes, iters=iters, seed=seed,
                             enforce_bounds=not quick)

    topology_seeds = topology_seeds_of(result)
    n_topo = len(topology_seeds)
    shared_topology_indices = audit.draw_shared_topology_indices(
        n_topo=n_topo, iters=iters, seed=seed)

    units = {q: extract_quantity_units(result, q) for q in QUANTITY_ARTIFACT_KEY}
    standalone = {
        q: standalone_distribution(units[q], shared_topology_indices=shared_topology_indices, seed=seed)
        for q in units
    }
    loto = {q: leave_one_topology_out(units[q], iters=iters, seed=seed) for q in units}

    within_var = {q: within_topology_variance(units[q], iters=iters, seed=seed) for q in units}
    heterogeneity = {
        q: topology_heterogeneity_ratio(standalone[q]["per_topology_points"], within_var[q])
        for q in units
    }
    n4_verdict, n4_detail = classify_n4(heterogeneity)

    n5_by_limb = {}
    for limb, (b_key, u_key) in LIMB_QUANTITIES.items():
        b_points = standalone[b_key]["per_topology_points"]
        u_points = standalone[u_key]["per_topology_points"]
        pairs = [(b, u) for b, u in zip(b_points, u_points)
                 if b is not None and u is not None and math.isfinite(b) and math.isfinite(u)]
        bx = [p[0] for p in pairs]
        ux = [p[1] for p in pairs]
        pearson_point = pearson_r(bx, ux)
        rank_point = spearman_r(bx, ux)
        assoc_bootstrap = bootstrap_association(
            units[b_key], units[u_key], shared_topology_indices=shared_topology_indices, seed=seed)
        n5_verdict, n5_detail = classify_n5(
            pearson_point, rank_point, assoc_bootstrap["pearson_interval_5_95"])
        n5_by_limb[limb] = {
            "pearson_point": pearson_point,
            "rank_point": rank_point,
            "bootstrap": assoc_bootstrap,
            "leave_one_topology_out": loto_association(b_points, u_points),
            "verdict": n5_verdict,
            "detail": n5_detail,
        }
    # Overall N5 evidence-matrix row: "raised" if raised for either limb,
    # else "compatible" if compatible for either, else "lowered" only if
    # lowered on both -- N5 is a live concern if it is live for EITHER limb.
    rank_order = {"raised": 2, "compatible": 1, "lowered": 0}
    n5_overall = max(n5_by_limb.values(), key=lambda v: rank_order[v["verdict"]])["verdict"]

    n1_verdict, n1_detail = classify_n1(
        b_topo_points=standalone["b_stable"]["per_topology_points"] + standalone["b_flex"]["per_topology_points"],
        u_topo_points=standalone["u_star_stable"]["per_topology_points"] + standalone["u_star_flex"]["per_topology_points"],
        u_interval=standalone["u_star_stable"]["interval_5_95"],
        u_loto_points=[e["point"] for e in loto["u_star_stable"]],
    )
    n2_verdict, n2_detail = classify_n2(
        standalone["u_star_stable"]["interval_5_95"], standalone["u_star_flex"]["interval_5_95"])

    topo_points_for_selection = {q: standalone[q]["per_topology_points"] for q in units}
    selection_summary = selection_instability_summary(result, topo_points_for_selection)
    selection_verdict, selection_detail = classify_selection_instability(selection_summary)

    evidence_matrix = {
        "N1_signed_normalizer_failure": {"verdict": n1_verdict, "detail": n1_detail},
        "N2_opposite_source_direction": {"verdict": n2_verdict, "detail": n2_detail},
        "N3_component_cancellation": {"verdict": "UNDISCRIMINATED_FROM_STORED_ARTIFACT",
                                       "detail": N3_STATEMENT},
        "N4_topology_heterogeneity": {"verdict": n4_verdict, "detail": n4_detail},
        "N5_comparator_scale_mismatch": {"verdict": n5_overall,
                                          "detail": "; ".join(f"{limb}: {v['detail']}" for limb, v in n5_by_limb.items())},
        "selection_instability": {"verdict": selection_verdict, "detail": selection_detail},
    }

    # Modification 6: nominate, never freeze. Purely descriptive candidates,
    # explicitly labeled non-binding -- this script decides no R4 branch.
    r4_candidates = []
    if n1_verdict == "raised":
        r4_candidates.append("normalizer redefinition or per-topology normalization (N1 raised)")
    if n5_overall == "raised":
        r4_candidates.append("a normalizer scale better matched to the focal one-Delta intervention (N5 raised)")
    if n4_verdict in ("dominant", "material"):
        r4_candidates.append("stratify or expand by topology before re-attempting a pooled normalizer (N4 " + n4_verdict + ")")
    if not r4_candidates:
        r4_candidates.append("no autopsy-nominated R4 direction; disposition remains open at the next review boundary")

    out = {
        "artifact_derived": True,
        "note": ("This script analyzes the SCALAR quantities recorded by the executed R3 code, "
                 "conditional on the correctness of that execution path. It is not itself a second "
                 "validation of the environment trajectories."),
        "input_artifact": {
            "path": ARTIFACT_RELATIVE_PATH,
            "sha256": EXPECTED_ARTIFACT_SHA256,
        },
        "quick_dev_run": bool(quick),
        "bootstrap_iters": int(iters),
        "bootstrap_seed": int(seed),
        "materiality_coefficient": audit.MATERIALITY_COEFFICIENT,
        "topology_seeds": topology_seeds,
        "sentinel": sentinel["checks"],
        "recomputed_t_m_bootstrap": sentinel["recomputed_t_m_bootstrap"],
        "recorded_t_m_bootstrap": result.get("t_m_bootstrap"),
        "section_a_standalone_distributions": {
            QUANTITY_LABEL[q]: standalone[q] for q in units
        },
        "section_a_leave_one_topology_out": {
            QUANTITY_LABEL[q]: loto[q] for q in units
        },
        "section_n4_topology_heterogeneity": {
            QUANTITY_LABEL[q]: {**heterogeneity[q], "within_topology_variance_per_topology": within_var[q]}
            for q in units
        },
        "section_n5_association": n5_by_limb,
        "section_g_selection_instability": selection_summary,
        "evidence_matrix": evidence_matrix,
        "r4_recommendations_non_binding": r4_candidates,
    }
    if quick:
        out.pop("evidence_matrix")
        out.pop("r4_recommendations_non_binding")
        out["note"] = ("QUICK_DEV_NOT_A_RESULT: --quick lowers bootstrap iterations for development "
                        "only. The evidence matrix and R4 recommendations are withheld so a "
                        "development run can never be mistaken for the real one.")
    return out


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if not math.isfinite(v):
            return str(v)
        return f"{v:.6f}"
    return str(v)


def render_markdown(out: dict) -> str:
    lines = ["# D7.S normalizer autopsy", "", out["note"], ""]
    lines.append(f"Input artifact: `{out['input_artifact']['path']}` "
                 f"(sha256 `{out['input_artifact']['sha256'][:16]}...`)")
    lines.append(f"Bootstrap: iters={out['bootstrap_iters']} seed={out['bootstrap_seed']} "
                 f"quick_dev_run={out['quick_dev_run']}")
    lines.append("")
    lines.append("## Sentinel (Modification 2)")
    lines.append("")
    lines.append("| condition | ok | detail |")
    lines.append("|---|---|---|")
    for name, c in out["sentinel"].items():
        lines.append(f"| {name} | {c['ok']} | {c['detail']} |")
    lines.append("")

    if "section_a_standalone_distributions" in out:
        lines.append("## Section A -- standalone distributions")
        lines.append("")
        lines.append("| quantity | point | 5th pct | 95th pct | min | max | +/-/0 |")
        lines.append("|---|---|---|---|---|---|---|")
        for label, d in out["section_a_standalone_distributions"].items():
            sc = d["sign_counts"]
            lines.append(
                f"| {label} | {_fmt(d['point'])} | {_fmt(d['interval_5_95'][0])} | "
                f"{_fmt(d['interval_5_95'][1])} | {_fmt(d['min'])} | {_fmt(d['max'])} | "
                f"{sc['positive']}/{sc['negative']}/{sc['zero']} |"
            )
        lines.append("")

    if "evidence_matrix" in out:
        lines.append("## Evidence matrix")
        lines.append("")
        lines.append("| explanation | verdict |")
        lines.append("|---|---|")
        for name, e in out["evidence_matrix"].items():
            lines.append(f"| {name} | {e['verdict']} |")
        lines.append("")
        lines.append("Do not force exactly one explanation to win (Modification 4).")
        lines.append("")
        lines.append("## R4 recommendations (non-binding, Modification 6)")
        lines.append("")
        for c in out["r4_recommendations_non_binding"]:
            lines.append(f"- {c}")
        lines.append("")
        lines.append("The final R4 freeze or carrier retirement remains a scientific "
                      "disposition at the next review boundary; this script does not decide it.")
    else:
        lines.append("## QUICK_DEV_NOT_A_RESULT")
        lines.append("")
        lines.append("Evidence matrix and R4 recommendations withheld under --quick.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", default=str(PROJECT_ROOT / ARTIFACT_RELATIVE_PATH),
                         help="Path to the input artifact (default: the registered pooled artifact).")
    parser.add_argument("--out", required=True,
                         help="Output directory; writes d7s_normalizer_autopsy.json and .md there.")
    parser.add_argument("--quick", action="store_true",
                         help="DEVELOPMENT ONLY: lowers bootstrap iterations and REFUSES to emit "
                              "the evidence matrix or R4 recommendations. Never a result.")
    args = parser.parse_args()

    iters = QUICK_ITERS if args.quick else audit.BOOTSTRAP_ITERS
    seed = audit.BOOTSTRAP_SEED

    out = run_autopsy(artifact_path=Path(args.artifact), iters=iters, seed=seed, quick=args.quick)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "d7s_normalizer_autopsy.json"
    md_path = out_dir / "d7s_normalizer_autopsy.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=audit._json_default)
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write(render_markdown(out))
    print(json.dumps({"json": str(json_path), "markdown": str(md_path)}))


if __name__ == "__main__":
    main()
