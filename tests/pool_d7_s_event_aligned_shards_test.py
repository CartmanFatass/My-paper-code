"""Focused tests for the D7.S event-aligned per-topology shard pooler.

The pooling contract: a shard is `audit_d7_s_event_aligned.py`'s `main()` run
over one or more whole topology seeds (never a split episode set), so pooling
N seed-disjoint shards must reproduce EXACTLY what one monolithic run over the
union of their topology seeds would have produced -- same
`assemble_audit_result` call, same branch, same bootstrap numbers -- and must
not depend on what order the shards are listed in (section 8's bootstrap
resamples topologies by list POSITION, so pooling order-invariance requires
re-sorting by topology seed before assembly, not just reproducing the same
set of topologies).

Every scientific field is recomputed by the audit module's own
`assemble_audit_result`, imported (never copied). Anything whose identity
cannot be proven -- mismatched contract, an unflagged smoke shard, overlapping
topology seeds, a seed union outside the two frozen sets -- is refused via
SystemExit, not silently pooled.
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, _ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


audit = _load("audit_d7_s_event_aligned")
pooling = _load("pool_d7_s_event_aligned_shards")


def _fast_t_m_bootstrap(monkeypatch, audit_module, iters=20):
    """`compute_t_m_bootstrap` at its frozen default (10,000 iters) is too
    slow for a focused test; monkeypatched down exactly as the driver tests
    in `tests/audit_d7_s_event_aligned_test.py` (section 9) do. Every
    fixture here is DEGENERATE (identical value at every topology/event), so
    resampling introduces no variance regardless of iteration count -- the
    override changes only runtime, never the asserted numbers. Takes the
    module object explicitly because `pool_d7_s_event_aligned_shards.py`
    loads its OWN independent copy of the audit module (a fresh
    `importlib.util.module_from_spec`, not the same object as this test
    file's `audit`), so patching one does not patch the other."""
    real = audit_module.compute_t_m_bootstrap
    monkeypatch.setattr(
        audit_module, "compute_t_m_bootstrap",
        lambda **kw: real(**{**kw, "iters": iters}))


def _degenerate_unit(value):
    """One degenerate single-candidate event: select == eval_set == value,
    eval_keep == 0, matching `_degenerate_topology_units` in the audit
    module's own test suite -- a topology's contribution is exactly `value`
    regardless of which sub-index bootstrap resampling draws."""
    return {"candidates": {"only": {"select": [value], "eval_set": [value]}},
            "eval_keep": [0.0]}


def _topology_result(seed, *, d_a, u_stable, u_flex, qualifying=4,
                      qualifying_calibration=None, qualifying_audit=None,
                      invalidated_pairs=None, arm_distinctness_pairs=None,
                      episode_worlds=None,
                      attempted_calibration=None, attempted_audit=None):
    """One synthetic `run_topology_audit`-shaped result -- exactly the shape
    `topology_unit_for_serialization` and the rest of `main()`'s per-topology
    arrays consume.

    2026-07-28 guard-gap repair: the original builder could only express
    states where `qualifying_calibration_episodes == qualifying_audit_episodes`,
    `invalidated_pairs == []`, and one fixed distinct-by-construction
    `arm_distinctness_pairs` entry -- every state a swapped/dropped whitelist
    key in `_reconstruct_topology_result` would corrupt was indistinguishable
    from the correct one under the old fixture. `qualifying_calibration`/
    `qualifying_audit` (falling back to `qualifying` when unset, so every
    existing call site is unchanged), `invalidated_pairs` and
    `arm_distinctness_pairs` now let a caller build an asymmetric,
    non-vacuous state on purpose."""
    qc = qualifying if qualifying_calibration is None else qualifying_calibration
    qa = qualifying if qualifying_audit is None else qualifying_audit
    # `episodes_attempted` is a DIFFERENT quantity from `qualifying`: the
    # freshness sentinel's `registered_episode_counts` condition reads the
    # former, support reads the latter. The fixture used to write `qualifying`
    # into both, so no test could express "attempted the registered volume,
    # only some qualified" -- the ordinary real case.
    ac = audit.N_CALIBRATION_EPISODES if attempted_calibration is None else attempted_calibration
    aa = audit.N_AUDIT_EPISODES if attempted_audit is None else attempted_audit
    if arm_distinctness_pairs is None:
        at_te = {0: 1, 1: 0}
        before_leave = {0: 0, 1: 1}
        arm_distinctness_pairs = [(at_te, before_leave)]
    result = {
        "topology_record": {
            "topology_seed": seed,
            "ground_bs": [[0.0, 0.0, 0.0]],
            "charging_stations": [[0.0, 0.0, 0.0]],
            "coordinate_hash": f"hash-{seed}",
            "procedure_version": audit.TOPOLOGY_PROCEDURE_VERSION,
        },
        "calibration_report": {"episodes_attempted": ac, "qualifying": qc},
        "audit_report": {"episodes_attempted": aa, "qualifying": qa},
        "audit_events": [],
        "qualifying_calibration_episodes": qc,
        "qualifying_audit_episodes": qa,
        "invalidated_pairs": invalidated_pairs if invalidated_pairs is not None else [],
        "arm_distinctness_pairs": arm_distinctness_pairs,
        "calibration_units_d_a": [_degenerate_unit(d_a)],
        "audit_units_stable": [_degenerate_unit(u_stable)],
        "audit_units_flex": [_degenerate_unit(u_flex)],
    }
    if episode_worlds is not None:
        result["episode_worlds"] = episode_worlds
    return result


def _write_shard(tmp_path, name, topology_results, *, smoke=False, contract_id=None,
                  overrides=None, r4_population=False):
    """Builds one shard JSON file via the Task-A writer path: the real
    `topology_unit_for_serialization` function plus the same surrounding
    dict shape `main()` assembles (data plumbing only, no branch logic --
    that stays exclusively in `assemble_audit_result`).

    `overrides` replaces any top-level shard key after assembly. It exists
    because `contract_id` used to be the only field this builder could vary,
    while `_assert_identity` quantifies over all of `CONTRACT_IDENTITY_FIELDS`
    -- so `contract` and `procedure_version` could be dropped from that tuple
    with the whole file green. A fixture builder with no affordance for a
    field is why that field goes untested; give it the affordance.

    `r4_population=True` writes the `r4_contract`/`r4_population_namespace`
    identity fields that only `audit_d7_s_event_aligned.py --population r4`
    produces. Default False, so the paired negative -- a shard produced
    WITHOUT the flag -- is what the unmodified builder gives you."""
    seeds = [r["topology_record"]["topology_seed"] for r in topology_results]
    shard = {
        "contract": audit.CONTRACT_PATH,
        "contract_id": contract_id if contract_id is not None else audit.CONTRACT_ID,
        "procedure_version": audit.TOPOLOGY_PROCEDURE_VERSION,
        "topology_seeds": seeds,
        "smoke": smoke,
        "note": "SMOKE_NOT_A_RESULT" if smoke else "Real orchestration run.",
        "topology_records": [r["topology_record"] for r in topology_results],
        "calibration_reports": [r["calibration_report"] for r in topology_results],
        "audit_reports": [r["audit_report"] for r in topology_results],
        "audit_events": [r["audit_events"] for r in topology_results],
        "topology_units": [audit.topology_unit_for_serialization(r) for r in topology_results],
        "topology_hash_failures": [],
        "r4_contract": audit.R4_CONTRACT_PATH if r4_population else None,
        "r4_population_namespace": (audit.R4_POPULATION_NAMESPACE
                                     if r4_population else None),
    }
    shard.update(overrides or {})
    path = tmp_path / name
    with path.open("w", encoding="utf-8") as fh:
        json.dump(shard, fh, ensure_ascii=False, default=audit._json_default)
    return str(path)


def _load_shards(paths):
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


# =============================================================================
# 1. Round-trip identity: pooled output equals the direct in-memory call
# =============================================================================

def test_pooled_output_equals_direct_assemble_audit_result(tmp_path, monkeypatch):
    """Six topologies (the frozen `MIN_SUPPORT_TOPOLOGIES` minimum), each at
    exactly `qualifying=4` (the frozen `MIN_SUPPORT_EPISODES_PER_TOPOLOGY`
    minimum) -- support is met only if EVERY topology's
    `qualifying_calibration_episodes`/`qualifying_audit_episodes` survives
    the JSON round trip, so a dropped or defaulted field here would flip
    `support_ok` and the branch, not just fail silently."""
    _fast_t_m_bootstrap(monkeypatch, audit)
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)

    # d_a=6.0 lands PART_A_CONFORMANCE_UNRESOLVED at the absolute anchor
    # (hand-worked in `tests/audit_d7_s_event_aligned_test.py`'s
    # `test_driver_part_a_unresolved_does_not_relabel_the_source_branch`),
    # which must NOT relabel the branch away from PERSISTENCE_NECESSARY_
    # SOURCE -- d_a=0.0 would instead land PART_A_CONTRADICTION (branch 4),
    # a different code path this test is not exercising. In practice branch
    # 1 (INVALID_EVENT_ALIGNED_AUDIT, asserted below) wins regardless, since
    # this fixture has no `component_audit` key at all.
    topo = [
        _topology_result(2000 + i, d_a=6.0,
                          u_stable=-2.0, u_flex=2.0)
        for i in range(6)
    ]
    p1 = _write_shard(tmp_path, "s1.json", topo[:3])
    p2 = _write_shard(tmp_path, "s2.json", topo[3:])
    shards = _load_shards([p1, p2])

    pooled = pooling.pool(shards, paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, [])

    assert pooled["branch"] == expected["branch"]
    # Ruling 2026-07-27 (COMPONENT_INVARIANCE tri-state): a run that is not
    # normalizer-forced-degenerate and never performed the mandatory
    # primary-G component audit is a measurement invalidity -- branch 1,
    # not a later branch. The pooler is production and so takes the
    # fail-closed default, which is why this fixture now lands there.
    # The property this test exists for -- pooled output equals direct
    # assembly -- is asserted above and is unchanged.
    assert pooled["branch"] == "INVALID_EVENT_ALIGNED_AUDIT"
    assert pooled["u_star_bootstrap"] == expected["u_star_bootstrap"]
    assert pooled["part_a"]["verdict"] == expected["part_a"]["verdict"]
    assert pooled["support"] == expected["support"]
    assert pooled["conformance"]["ok"] == expected["conformance"]["ok"] is True
    assert pooled["conformance"]["invalidated_pairs_count"] == 0
    assert pooled["topology_records"] == [
        r["topology_record"] for r in sorted(topo, key=lambda r: r["topology_record"]["topology_seed"])
    ]


# =============================================================================
# 2. Argument-order invariance
# =============================================================================

def test_pooling_is_invariant_to_shard_argument_order(tmp_path, monkeypatch):
    """Pooling [c, b, a] must equal pooling [a, b, c] field for field (except
    `pooling_provenance`, which legitimately echoes the argument order given).
    This is the load-bearing property named in the module docstring: the
    hierarchical bootstrap resamples topologies by list position, so an
    order-dependent pooler would silently draw a different bootstrap sample
    depending on how the shards happened to be listed on the command line.

    Measured regression (2026-07-27 sweep): the original six topologies here
    all carried the IDENTICAL degenerate value set, so permuting shard order
    permuted which POSITION held a given topology without changing what
    value sat at any position the bootstrap actually reads by index --
    order literally cannot matter for a construction this degenerate, so a
    pooler that forgot to re-sort by topology seed before assembly (instead
    silently keeping shard/argument order) would still pass. Each topology
    below now carries its own distinct value set, so the bootstrap's
    per-position resample would draw genuinely different numbers depending
    on argument order unless the pooler re-sorts."""
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)

    topo = [
        _topology_result(3000 + i, d_a=0.05 + 0.03 * i,
                          u_stable=-2.0 + 0.4 * i, u_flex=1.0 + 0.3 * i)
        for i in range(6)
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:2])
    p2 = _write_shard(tmp_path, "b.json", topo[2:4])
    p3 = _write_shard(tmp_path, "c.json", topo[4:])

    forward = pooling.pool(_load_shards([p1, p2, p3]), paths=[p1, p2, p3], allow_any_seeds=True)
    backward = pooling.pool(_load_shards([p3, p2, p1]), paths=[p3, p2, p1], allow_any_seeds=True)

    forward.pop("pooling_provenance")
    backward.pop("pooling_provenance")
    assert forward == backward


# =============================================================================
# 3. Identity assertions: each one fires
# =============================================================================

def test_contract_id_mismatch_is_refused(tmp_path):
    p1 = _write_shard(tmp_path, "a.json",
                       [_topology_result(4001, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)])
    p2 = _write_shard(tmp_path, "b.json",
                       [_topology_result(4002, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)],
                       contract_id="SOME_OTHER_CONTRACT")
    with pytest.raises(SystemExit, match="contract_id"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def test_overlapping_topology_seeds_are_refused(tmp_path):
    p1 = _write_shard(tmp_path, "a.json",
                       [_topology_result(5001, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)])
    p2 = _write_shard(tmp_path, "b.json",
                       [_topology_result(5001, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)])
    with pytest.raises(SystemExit, match="overlap"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def _flat_pair(tmp_path, seed_a, seed_b, **kw_a):
    """Two minimal shards on distinct seeds. `kw_a` applies to the first only."""
    make = lambda n, s, **kw: _write_shard(
        tmp_path, n, [_topology_result(s, d_a=0.0,
                                        u_stable=1.0, u_flex=1.0)], **kw)
    return make("a.json", seed_a, **kw_a), make("b.json", seed_b)


def test_smoke_shard_is_refused_without_allow_smoke(tmp_path):
    """Matches the gate's own wording, not the bare word "smoke".

    A guard-deletion sweep on 2026-07-27 found this file green with EITHER
    smoke guard disabled, because the two of them mask each other: this
    fixture is a mixed pair, so whichever gate survives refuses it, and both
    messages contain "smoke". The match must name one gate."""
    p1, p2 = _flat_pair(tmp_path, 6001, 6002, smoke=True)
    with pytest.raises(SystemExit, match="refusing to pool smoke shard"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def test_uniformly_smoke_shards_are_refused_without_allow_smoke(tmp_path):
    """The shape a real smoke run actually produces -- and the one that was
    never tested. Its sibling above pools a *mixed* pair, so the smoke-flag
    mismatch gate refused it regardless; deleting the `SMOKE_NOT_A_RESULT`
    gate left this file 8/8 green while `pool()` accepted a uniformly-smoke
    set and returned it with `smoke=True`. Measured, not inferred.

    The output does carry the flag onward, so a careful downstream reader
    could still see it -- but this gate is a refusal, not a label, and
    nothing tested that it refuses."""
    p1 = _write_shard(tmp_path, "a.json",
                       [_topology_result(6101, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)], smoke=True)
    p2 = _write_shard(tmp_path, "b.json",
                       [_topology_result(6102, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)], smoke=True)
    with pytest.raises(SystemExit, match="refusing to pool smoke shard"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def test_a_smoke_flag_mix_is_refused_even_when_smoke_is_allowed(tmp_path):
    """Unmasks the second gate by removing the first: with `allow_smoke=True`
    the `SMOKE_NOT_A_RESULT` gate stands down, so only the uniformity gate can
    refuse a mixed pair. Half a real result and half a smoke result is not a
    result at any flag setting."""
    p1, p2 = _flat_pair(tmp_path, 6201, 6202, smoke=True)
    with pytest.raises(SystemExit, match="smoke-flag mismatch"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2],
                     allow_smoke=True, allow_any_seeds=True)


@pytest.mark.parametrize("field, wrong", [
    ("contract", "docs/research/designs/SOME_OTHER_CONTRACT.md"),
    ("contract_id", "SOME_OTHER_CONTRACT"),
    ("procedure_version", "not-the-frozen-procedure"),
])
def test_every_contract_identity_field_is_checked(tmp_path, field, wrong):
    """`_assert_identity` quantifies over all of `CONTRACT_IDENTITY_FIELDS`;
    only `contract_id` was ever varied, so dropping either of the other two
    from that tuple left the file green. Read the guard's own quantifier and
    range over it."""
    assert field in pooling.CONTRACT_IDENTITY_FIELDS
    p1, p2 = _flat_pair(tmp_path, 4101, 4102, overrides={field: wrong})
    with pytest.raises(SystemExit, match=field):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def test_pooling_fewer_than_two_shards_is_refused(tmp_path):
    """Pooling one shard would silently relabel a partial run as a pooled
    result. The guard existed and nothing exercised it."""
    p1, _ = _flat_pair(tmp_path, 4201, 4202)
    with pytest.raises(SystemExit, match="at least two shards"):
        pooling.pool(_load_shards([p1]), paths=[p1], allow_any_seeds=True)


def test_internally_inconsistent_shard_columns_are_refused(tmp_path):
    """The five per-topology columns are zipped, and `zip` truncates in
    silence -- a short column would drop topologies out of the pooled result
    with no error at all. Untested until 2026-07-27."""
    p1, p2 = _flat_pair(tmp_path, 4301, 4302)
    with open(p1, encoding="utf-8") as fh:
        shard = json.load(fh)
    shard["audit_events"] = []          # one column short, the rest intact
    with open(p1, "w", encoding="utf-8") as fh:
        json.dump(shard, fh, ensure_ascii=False)
    with pytest.raises(SystemExit, match="mismatched lengths"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)


def test_seed_union_not_a_frozen_set_is_refused(tmp_path):
    p1 = _write_shard(tmp_path, "a.json",
                       [_topology_result(7001, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)])
    p2 = _write_shard(tmp_path, "b.json",
                       [_topology_result(7002, d_a=0.0,
                                          u_stable=1.0, u_flex=1.0)])
    with pytest.raises(SystemExit, match="frozen"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])  # allow_any_seeds defaults False


def test_r3_topology_unit_is_refused_by_the_r4_pooler(tmp_path):
    """Freshness sentinel condition 5 (contract section 3): "no R3 topology
    unit is accepted by the R4 pooler." The REAL registered
    `TOPOLOGY_SEEDS_INITIAL` (R3's 8 seeds) must be refused even with NO
    override -- the frozen-set gate now accepts ONLY the R4 population,
    never R3's, which R3's own historical pooled artifacts under logs/ never
    needed anyway (they are already complete)."""
    seeds = list(audit.TOPOLOGY_SEEDS_INITIAL)
    topo = [
        _topology_result(s, d_a=0.35, u_stable=-1.0, u_flex=1.0)
        for s in seeds
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:4])
    p2 = _write_shard(tmp_path, "b.json", topo[4:])

    with pytest.raises(SystemExit, match="R3 topology unit"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])  # allow_any_seeds defaults False


def test_registered_r4_seed_set_is_accepted_without_allow_any_seeds(tmp_path, monkeypatch):
    """The positive case of the frozen-set gate: the REAL registered
    `TOPOLOGY_SEEDS_R4` (8 seeds) pools cleanly with no override, proving the
    membership check accepts the actual frozen R4 set and not merely that it
    rejects everything else (R3's included, per the paired negative above).

    Both shards must now be produced as DECLARED R4 population members
    (`--population r4`), which is what `r4_population=True` writes."""
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    topo = [
        _topology_result(s, d_a=0.35, u_stable=-1.0, u_flex=1.0)
        for s in seeds
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:4], r4_population=True)
    p2 = _write_shard(tmp_path, "b.json", topo[4:], r4_population=True)

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])

    assert pooled["topology_seeds"] == seeds
    # R1: the identity fields are propagated into the pooled artifact, so it
    # carries the proof it belongs to the R4 population.
    assert pooled["r4_contract"] == audit.R4_CONTRACT_PATH
    assert pooled["r4_population_namespace"] == audit.R4_POPULATION_NAMESPACE
    # ...and the pooled artifact passed `r4_freshness_sentinel` on the way
    # out (the pooler SystemExits otherwise), which is checkable here too.
    assert audit.r4_freshness_sentinel(pooled)[0] is True
    # Ruling 2026-07-27 (COMPONENT_INVARIANCE tri-state): a run that is not
    # normalizer-forced-degenerate and never performed the mandatory
    # primary-G component audit is a measurement invalidity -- branch 1,
    # not a later branch. The pooler is production and so takes the
    # fail-closed default, which is why this fixture now lands there.
    assert pooled["branch"] == "INVALID_EVENT_ALIGNED_AUDIT"
    assert pooled["branch_reason"] == "MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING"


# =============================================================================
# 3b. R1: the sharded production route must EARN R4 identity, and the pooled
# artifact must pass the freshness sentinel before it is returned.
# =============================================================================

def _r4_shard_pair(tmp_path, monkeypatch, *, r4_population=True, **topo_kwargs):
    """Two seed-disjoint shards spanning the whole frozen R4 population."""
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    topo = [_topology_result(s, d_a=0.35, u_stable=-1.0, u_flex=1.0, **topo_kwargs)
            for s in seeds]
    p1 = _write_shard(tmp_path, "a.json", topo[:4], r4_population=r4_population)
    p2 = _write_shard(tmp_path, "b.json", topo[4:], r4_population=r4_population)
    return [p1, p2]


def test_a_shard_without_the_population_flag_makes_the_pooler_refuse(tmp_path, monkeypatch):
    """Paired negative for the test above. Measured defect: the formal R4 run
    is planned as one shard per topology, and identity was earned only when
    ONE process's whole seed list equalled `TOPOLOGY_SEEDS_R4` -- so every
    shard ran under the legacy R3 `contract_id` namespace, the pooled
    artifact carried `r4_contract=None`/`r4_population_namespace=None` and
    was self-labelled "NOT R4 conclusion-bearing", while the pooler still
    printed the conclusion-bearing `D7_S_EVENT_ALIGNED_BRANCH=` line.

    A shard produced without `--population r4` carries no proof it belongs to
    the R4 population and the pool must be REFUSED, not relabelled."""
    paths = _r4_shard_pair(tmp_path, monkeypatch, r4_population=False)
    with pytest.raises(SystemExit, match="carries no proof it belongs to the R4 population"):
        pooling.pool(_load_shards(paths), paths=paths)


def test_one_undeclared_shard_among_declared_ones_is_enough_to_refuse(tmp_path, monkeypatch):
    """Not "some shard proves it" -- EVERY shard must. One undeclared shard in
    an otherwise declared pool is refused, and the message names that shard."""
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    topo = [_topology_result(s, d_a=0.35, u_stable=-1.0, u_flex=1.0) for s in seeds]
    p1 = _write_shard(tmp_path, "declared.json", topo[:4], r4_population=True)
    p2 = _write_shard(tmp_path, "undeclared.json", topo[4:], r4_population=False)

    with pytest.raises(SystemExit, match=r"undeclared\.json carries no proof"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])


def test_pooler_fails_closed_when_the_pooled_artifact_fails_the_sentinel(tmp_path, monkeypatch):
    """R1: `r4_freshness_sentinel` was defined and called from NO production
    path at all -- contract section 3 says "fail closed unless" and there was
    no executable closure. The pooler now runs it on its own output.

    Driven through condition 5 (`registered_episode_counts`), which no other
    pooler gate touches: every shard is a properly declared R4 member with a
    disjoint, complete seed union, so identity, smoke, disjointness and the
    frozen-set gate all pass -- only the sentinel can stop this pool. The
    topologies attempted 2 calibration episodes instead of the registered 8,
    the exact volume defect R2 names."""
    paths = _r4_shard_pair(tmp_path, monkeypatch, attempted_calibration=2)
    with pytest.raises(SystemExit,
                       match=r"freshness sentinel FAILED.*registered_episode_counts"):
        pooling.pool(_load_shards(paths), paths=paths)


def test_a_conforming_r4_pool_passes_the_sentinel_it_is_gated_on(tmp_path, monkeypatch):
    """The positive half of the gate above: with the registered episode
    volume attempted, the same pool succeeds. Without this, the sentinel call
    could be refusing everything and the negative test would not notice."""
    paths = _r4_shard_pair(tmp_path, monkeypatch)
    pooled = pooling.pool(_load_shards(paths), paths=paths)
    ok, detail = audit.r4_freshness_sentinel(pooled)
    assert ok is True, detail


# =============================================================================
# 3c. R1, end to end: shards produced by the REAL `main()` production path,
# pooled by the REAL pooler. Every fixture above hand-assembles the shard
# dict; this one does not, so it is the only test that proves the production
# route from CLI to pooled artifact can earn R4 identity at all.
# =============================================================================

def _stub_topology_result(seed):
    """Exactly the shape `run_topology_audit` returns, reduced to what
    `main()` and `assemble_audit_result` read. Zero qualifying episodes keeps
    `support_ok` False so no 10,000-iteration bootstrap runs -- the freshness
    sentinel is indifferent to the branch."""
    return {
        "topology_record": {"topology_seed": seed, "coordinate_hash": f"h{seed}",
                             "procedure_version": audit.TOPOLOGY_PROCEDURE_VERSION},
        "calibration_report": {"episodes_attempted": audit.N_CALIBRATION_EPISODES,
                                "qualifying": 0},
        "audit_report": {"episodes_attempted": audit.N_AUDIT_EPISODES, "qualifying": 0},
        "audit_events": [],
        "qualifying_calibration_episodes": 0, "qualifying_audit_episodes": 0,
        "invalidated_pairs": [], "arm_distinctness_pairs": [],
        "calibration_units_d_a": [], "audit_units_stable": [], "audit_units_flex": [],
        "episode_worlds": [],
    }


def _main_shard(monkeypatch, tmp_path, name, seeds, *, declared: bool):
    """Runs the REAL `audit_d7_s_event_aligned.main()` for `seeds` and returns
    the path of the shard JSON it wrote."""
    monkeypatch.setattr(audit, "build_config", lambda: None)
    monkeypatch.setattr(
        audit, "run_topology_audit",
        lambda config, *, topology_seed, **kw: _stub_topology_result(topology_seed))
    out_dir = tmp_path / name
    argv = ["audit_d7_s_event_aligned.py", "--out", str(out_dir)]
    if declared:
        argv += ["--population", "r4"]
    argv += ["--topology-seeds"] + [str(s) for s in seeds]
    monkeypatch.setattr(sys, "argv", argv)
    audit.main()
    return str(out_dir / "d7_s_event_aligned.json")


def test_shards_from_the_real_main_pool_into_an_artifact_that_earns_r4_identity(
        tmp_path, monkeypatch):
    """R1 end to end. Two declared shards, four topologies each, produced by
    the real `main()`; the real `pool()` accepts them, propagates the identity
    fields, and the pooled artifact passes `r4_freshness_sentinel`."""
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    p1 = _main_shard(monkeypatch, tmp_path, "s1", seeds[:4], declared=True)
    p2 = _main_shard(monkeypatch, tmp_path, "s2", seeds[4:], declared=True)

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])

    assert pooled["topology_seeds"] == seeds
    assert pooled["r4_population_namespace"] == audit.R4_POPULATION_NAMESPACE
    ok, detail = audit.r4_freshness_sentinel(pooled)
    assert ok is True, detail


def test_shards_from_main_without_the_population_flag_are_refused_by_the_pooler(
        tmp_path, monkeypatch):
    """The paired negative, through the same production path: one shard run
    WITHOUT `--population r4` -- exactly what the formal run would have
    produced before this repair -- and the pool is refused rather than
    quietly producing a branch string for an artifact with no R4 provenance."""
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    p1 = _main_shard(monkeypatch, tmp_path, "s1", seeds[:4], declared=True)
    p2 = _main_shard(monkeypatch, tmp_path, "s2", seeds[4:], declared=False)

    with pytest.raises(SystemExit, match="carries no proof it belongs to the R4 population"):
        pooling.pool(_load_shards([p1, p2]), paths=[p1, p2])


# =============================================================================
# 3d. The pooler's own CLI entry point. `pool()` is well covered; `main()` --
# argument parsing, file reading, the `D7_S_EVENT_ALIGNED_BRANCH=` line, the
# artifact write -- was invoked by no test. That is the shape the R1 defect
# had one level down: a production route nothing exercises, so nothing
# asserts that the route the real run takes produces a conforming artifact.
# =============================================================================

def _run_pooler_main(monkeypatch, tmp_path, shard_paths, out_name="pooled"):
    """Drives the REAL `pool_d7_s_event_aligned_shards.main()` through argv and
    returns `(pooled_artifact_from_disk, stdout_text)`."""
    out_dir = tmp_path / out_name
    monkeypatch.setattr(
        sys, "argv",
        ["pool_d7_s_event_aligned_shards.py", "--shards", *shard_paths, "--out", str(out_dir)])
    pooling.main()
    with (out_dir / "d7_s_event_aligned.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def test_pooler_main_writes_a_conforming_r4_artifact(tmp_path, monkeypatch, capsys):
    """The pooler CLI, end to end: shards produced by the real audit `main()`
    on the declared R4 path, pooled by the real pooler `main()`, and the
    artifact read back OFF DISK -- never the dict `pool()` returned in
    memory. The R4 identity fields must survive the JSON round trip and the
    artifact must pass the freshness sentinel."""
    _fast_t_m_bootstrap(monkeypatch, pooling.audit)
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    p1 = _main_shard(monkeypatch, tmp_path, "s1", seeds[:4], declared=True)
    p2 = _main_shard(monkeypatch, tmp_path, "s2", seeds[4:], declared=True)

    pooled = _run_pooler_main(monkeypatch, tmp_path, [p1, p2])

    assert pooled["topology_seeds"] == seeds
    assert pooled["r4_contract"] == audit.R4_CONTRACT_PATH
    assert pooled["r4_population_namespace"] == audit.R4_POPULATION_NAMESPACE
    ok, detail = audit.r4_freshness_sentinel(pooled)
    assert ok is True, detail

    # The conclusion-bearing line the CLI prints is now printed only for an
    # artifact that cleared the sentinel -- which is the whole point of R1.
    out = capsys.readouterr().out
    assert f"D7_S_EVENT_ALIGNED_BRANCH={pooled['branch']}" in out


def test_pooler_main_exits_nonzero_on_an_undeclared_shard(tmp_path, monkeypatch, capsys):
    """Paired negative for the CLI. One shard produced WITHOUT
    `--population r4` must make the entry point exit NONZERO and write no
    artifact -- not warn, not relabel, and above all not reach the
    `D7_S_EVENT_ALIGNED_BRANCH=` line. A `SystemExit` carrying a string
    message exits 1."""
    seeds = list(audit.TOPOLOGY_SEEDS_R4)
    p1 = _main_shard(monkeypatch, tmp_path, "s1", seeds[:4], declared=True)
    p2 = _main_shard(monkeypatch, tmp_path, "s2", seeds[4:], declared=False)

    out_dir = tmp_path / "pooled_bad"
    monkeypatch.setattr(
        sys, "argv",
        ["pool_d7_s_event_aligned_shards.py", "--shards", p1, p2, "--out", str(out_dir)])

    with pytest.raises(SystemExit) as excinfo:
        pooling.main()

    assert excinfo.value.code != 0
    assert "carries no proof it belongs to the R4 population" in str(excinfo.value)
    assert not (out_dir / "d7_s_event_aligned.json").exists()
    assert "D7_S_EVENT_ALIGNED_BRANCH=" not in capsys.readouterr().out


# =============================================================================
# 4. Numpy round-trip losslessness
# =============================================================================

def test_numpy_round_trip_is_lossless_on_tricky_magnitudes():
    """A unit array with values that expose truncation or dtype defects:
    `0.1 + 0.2` (the classic float-repr trap), very large and very small
    magnitudes. `_json_default` (numpy -> list) and `_rebuild_unit_arrays`
    (list -> numpy) must round-trip every one of them bit-exact -- checked
    with `assert_array_equal`, not `approx`, so any precision loss (e.g. a
    stray `float32` cast, or serializing via `str()`/rounding) fails this
    test."""
    values = np.array([0.1 + 0.2, 1e-300, 1e300, -1e-16, 123456789.123456789,
                        -0.0, 3.141592653589793])
    unit = {"candidates": {"z": {"select": values, "eval_set": values}},
            "eval_keep": values}

    dumped = json.loads(json.dumps(unit, default=audit._json_default))
    rebuilt = pooling._rebuild_unit_arrays(dumped)

    assert rebuilt["candidates"]["z"]["select"].dtype == np.float64
    np.testing.assert_array_equal(rebuilt["candidates"]["z"]["select"], values)
    np.testing.assert_array_equal(rebuilt["candidates"]["z"]["eval_set"], values)
    np.testing.assert_array_equal(rebuilt["eval_keep"], values)


# =============================================================================
# 5. `_reconstruct_topology_result` key-whitelist guards
#
# Each test compares the POOLED result (JSON round trip through
# `_reconstruct_topology_result`) against `audit.assemble_audit_result`
# called DIRECTLY on the original in-memory `topo` list -- a genuinely
# independent code path that never goes through the pooler's whitelist, so
# a swapped or dropped key in the reconstruction is visible even though
# `assemble_audit_result` itself is trusted and never reimplemented. Every
# fixture is built asymmetric/non-vacuous on purpose (see `_topology_result`
# docstring) so the corrupted state is numerically DIFFERENT from the
# correct one, not merely differently-labeled.
# =============================================================================

# R3's `test_calibration_limb_assignment_is_not_swapped` (Gap 1) guarded the
# `calibration_units_stable`/`calibration_units_flex` reconstruction keys
# against a stable/flex swap. R4 deleted both fields from `topology_unit_
# for_serialization` and `_reconstruct_topology_result`'s whitelist (contract
# sections 8/10: the R3 `B_m` constructive-vs-null contrast has no
# conclusion-bearing role in R4) -- the property is genuinely gone, not
# preserved elsewhere, so the test is deleted with the fields rather than
# kept pointing at keys that no longer exist. `calibration_units_d_a`
# (Part-A's own surviving accumulator) has no limb-swap failure mode to
# guard against -- it is a single unlabeled quantity, not a stable/flex pair.


def test_pooled_topology_hash_failures_are_not_dropped(tmp_path):
    """Gap 2: a shard's top-level `topology_hash_failures` (one topology
    that failed the pinned-coordinate hash assert and so contributed no
    `topology_units` entry) must still reach the pooled
    `assemble_audit_result` call. Two clean 1-episode topologies (qualifying
    below `MIN_SUPPORT_EPISODES_PER_TOPOLOGY` so support fails fast and the
    T_m bootstrap never runs -- irrelevant to this guard) plus one shard
    that independently declares a hash failure for a THIRD topology seed
    that never produced a `topology_units` entry at all, matching what a
    real hash-assert failure looks like."""
    topo = [
        _topology_result(8101, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1),
        _topology_result(8102, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1),
    ]
    hash_failure = [{"topology_seed": 8103, "reason": "pinned-coordinate hash mismatch"}]
    p1 = _write_shard(tmp_path, "a.json", topo[:1])
    p2 = _write_shard(tmp_path, "b.json", topo[1:],
                       overrides={"topology_hash_failures": hash_failure})

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, hash_failure)

    # Independent literal: any non-empty topology_hash_failures makes
    # topology_hash_ok False, which alone makes conformance.ok False
    # (compute_conformance_ok's real conjunction).
    assert expected["conformance"]["topology_hash_ok"] is False
    assert expected["conformance"]["ok"] is False
    assert pooled["conformance"]["topology_hash_failures"] == hash_failure
    assert pooled["conformance"]["topology_hash_ok"] == expected["conformance"]["topology_hash_ok"] is False
    assert pooled["conformance"]["ok"] == expected["conformance"]["ok"] is False


def test_qualifying_calibration_and_audit_counts_are_not_swapped(tmp_path):
    """Gap 3: `qualifying_calibration_episodes` and `qualifying_audit_episodes`
    are thresholded INDEPENDENTLY by `check_minimum_support`
    (MIN_SUPPORT_EPISODES_PER_TOPOLOGY=4). Six topologies: all six qualify on
    calibration (4 episodes each), only three qualify on audit (4 vs 2) --
    an asymmetry the old fixture (`qualifying` sets both counts identically)
    could not express at all. A whitelist swap would report
    `calibration_topologies_ok=3, audit_topologies_ok=6` -- the exact
    opposite pair, not merely a different number."""
    topo = [
        _topology_result(8200 + i, d_a=0.0,
                          u_stable=1.0, u_flex=1.0,
                          qualifying_calibration=4,
                          qualifying_audit=4 if i < 3 else 2)
        for i in range(6)
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:3])
    p2 = _write_shard(tmp_path, "b.json", topo[3:])

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, [])

    # Independent literal, hand-counted from the fixture above: 6 topologies
    # clear the calibration threshold, only 3 clear the audit threshold.
    assert expected["support"]["detail"] == {
        "calibration_topologies_ok": 6, "audit_topologies_ok": 3}
    assert pooled["support"]["detail"] == expected["support"]["detail"] == {
        "calibration_topologies_ok": 6, "audit_topologies_ok": 3}


def test_invalidated_pairs_are_not_dropped(tmp_path):
    """Gap 4: a topology's own `invalidated_pairs`
    (`PrefixReplayMismatchError` records) must reach the pooled
    `invalidated_pairs_count`/`conformance.ok`. One topology carries one
    invalidated pair; conformance must go False on the strength of that
    single record alone (zero tolerance, per `compute_conformance_ok`'s
    docstring)."""
    one_invalidated = [{"episode_index": 0, "reason": "prefix replay mismatch"}]
    topo = [
        _topology_result(8301, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1,
                          invalidated_pairs=one_invalidated),
        _topology_result(8302, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1),
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:1])
    p2 = _write_shard(tmp_path, "b.json", topo[1:])

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, [])

    # Independent literal: exactly one invalidated pair was built above.
    assert expected["conformance"]["invalidated_pairs_count"] == 1
    assert expected["conformance"]["ok"] is False
    assert pooled["conformance"]["invalidated_pairs_count"] == expected["conformance"]["invalidated_pairs_count"] == 1
    assert pooled["conformance"]["ok"] == expected["conformance"]["ok"] is False


def test_arm_distinctness_pairs_are_not_dropped(tmp_path):
    """Gap 5: `arm_distinctness_check([])` returns True VACUOUSLY -- exactly
    what a populated-but-uniform pair list also returns, so the old fixture
    (its one hardcoded pair always had `at_te != before_leave`) could not
    have caught this drop even with a non-empty list: dropping to `[]` and
    keeping the always-distinct pair both read as conformant. Here every
    pair has `at_te == before_leave` (arms IDENTICAL at every certified
    event -- the actual defect this check exists to catch), so the correct
    pooled result is conformance-failing and the drop-to-`[]` mutation
    would flip it to vacuously conformant -- a real, not cosmetic,
    difference."""
    identical_pair = ({0: 1, 1: 0}, {0: 1, 1: 0})
    topo = [
        _topology_result(8401, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1,
                          arm_distinctness_pairs=[identical_pair]),
        _topology_result(8402, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1,
                          arm_distinctness_pairs=[identical_pair]),
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:1])
    p2 = _write_shard(tmp_path, "b.json", topo[1:])

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, [])

    # Independent literal: every pair built above is arm-identical, so the
    # spot check must fail (not the vacuous-empty-list True).
    assert expected["conformance"]["arm_distinct_ok"] is False
    assert expected["conformance"]["ok"] is False
    assert pooled["conformance"]["arm_distinct_ok"] == expected["conformance"]["arm_distinct_ok"] is False
    assert pooled["conformance"]["ok"] == expected["conformance"]["ok"] is False


def test_episode_worlds_are_not_dropped(tmp_path):
    """Lower-priority bonus gap: `episode_worlds` is reported
    (`episode_world_provenance`), never gated -- the code's own comment
    says so -- so this guards diagnostic reach only, not a branch or
    verdict. One topology carries one non-seed-controlled episode-world
    record; a drop to `[]` would silently erase it from the pooled
    provenance report."""
    world = [{"block": "audit", "episode_index": 0, "episode_seed": 8501,
              "fingerprint": "abc123", "seed_controls_generation": False}]
    topo = [
        _topology_result(8501, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1,
                          episode_worlds=world),
        _topology_result(8502, d_a=0.0,
                          u_stable=1.0, u_flex=1.0, qualifying=1),
    ]
    p1 = _write_shard(tmp_path, "a.json", topo[:1])
    p2 = _write_shard(tmp_path, "b.json", topo[1:])

    pooled = pooling.pool(_load_shards([p1, p2]), paths=[p1, p2], allow_any_seeds=True)
    expected = audit.assemble_audit_result(topo, [])

    # Independent literal: exactly one episode-world record was built above.
    assert expected["episode_world_provenance"]["episodes_recorded"] == 1
    assert expected["episode_world_provenance"]["all_seed_controlled"] is False
    assert pooled["episode_world_provenance"]["episode_worlds"] == world
    assert (pooled["episode_world_provenance"]["episodes_recorded"]
            == expected["episode_world_provenance"]["episodes_recorded"] == 1)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
