"""Pool per-topology D7.S event-aligned audit shards into the JSON one
monolithic `audit_d7_s_event_aligned.py` run would write.

The formal joint audit runs 8 topology seeds (or 16 under the one permissible
expansion, section 9 of the frozen contract); one process per topology gives
topology-level parallelism. Each shard is `audit_d7_s_event_aligned.py`'s
`main()` run with one or more `--topology-seeds` values -- sharding here is BY
WHOLE TOPOLOGY SEED, one or more seeds per shard, NEVER splitting episodes
within a topology (unlike the D7.S part-B persistence-margin pooler's
episode-tiling in `pool_d7_s_persistence_shards.py`, which does not apply to
this instrument).

Every shard's JSON already carries (Task A, `audit_d7_s_event_aligned.py`'s
`main()`) a complete, numerically lossless `topology_units` entry per topology
it successfully processed -- every key `assemble_audit_result` consumes
(`qualifying_calibration_episodes`, `qualifying_audit_episodes`,
`invalidated_pairs`, `arm_distinctness_pairs`, `calibration_units_stable`,
`calibration_units_flex`, `calibration_units_d_a`, `audit_units_stable`,
`audit_units_flex`), plus `topology_hash_failures` for topologies that failed
the pinned-coordinate hash assert. This pooler:

1. Refuses to pool anything whose identity is not proven (SystemExit on any
   violation): every shard shares the same `contract`/`contract_id`/
   `procedure_version`; every shard's `smoke` flag is False unless
   `--allow-smoke` is passed (pooling smoke shards -- SMOKE_NOT_A_RESULT -- is
   otherwise refused); every pair of shards' declared topology-seed sets is
   disjoint; the UNION of every shard's topology seeds equals one of the two
   frozen sets -- `TOPOLOGY_SEEDS_INITIAL` (20260726..33) or that set plus
   `TOPOLOGY_SEEDS_EXPANSION` (20260734..41) -- unless `--allow-any-seeds` is
   passed (development pooling only).
2. Reconstructs `topology_results` in ASCENDING topology-seed order
   REGARDLESS of shard/argument order -- deterministic and load-bearing, not
   cosmetic: section 8's hierarchical bootstrap resamples topologies by
   POSITION (`draw_shared_topology_indices` draws slot indices into the
   `topology_units` list; `hierarchical_bootstrap_quantity` indexes each
   quantity's per-topology unit list by that same slot), so the pooled
   `topology_results` order determines which topology's units land in which
   bootstrap slot. Sorting by topology seed before assembly makes the pooled
   result identical no matter what order `--shards` lists its paths in.
3. Rebuilds numpy `select`/`eval_set`/`eval_keep` arrays from their
   JSON-serialized lists, and reverses JSON's int-key-to-string coercion and
   tuple-to-list coercion on `arm_distinctness_pairs`' duty maps.
4. Calls `assemble_audit_result` (imported from the audit module, never
   reimplemented) on the reconstructed `topology_results` and pooled
   `topology_hash_failures`, and emits the same final JSON shape `main()`
   emits, plus a `pooling_provenance` block (shard paths and each shard's
   declared topology seeds).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "audit_d7_s_event_aligned", _HERE / "audit_d7_s_event_aligned.py")
audit = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, audit)
_SPEC.loader.exec_module(audit)

CONTRACT_IDENTITY_FIELDS = ("contract", "contract_id", "procedure_version")

FROZEN_SEED_SETS = (
    frozenset(audit.TOPOLOGY_SEEDS_INITIAL),
    frozenset(audit.TOPOLOGY_SEEDS_INITIAL) | frozenset(audit.TOPOLOGY_SEEDS_EXPANSION),
)


def _rebuild_unit_arrays(unit: dict) -> dict:
    """Rebuilds one calibration/audit bootstrap unit's numpy arrays from the
    JSON lists Task A wrote. `np.asarray(..., dtype=float)` on a JSON number
    list round-trips full double precision losslessly -- JSON numbers are
    decimal text and Python's float parser is correctly rounded, so a value
    like `0.1 + 0.2` survives the trip bit for bit. Any other key on the unit
    (e.g. an audit unit's own `invalidated_pairs` echo) passes through
    unchanged."""
    out = dict(unit)
    out["candidates"] = {
        z_id: {"select": np.asarray(c["select"], dtype=float),
               "eval_set": np.asarray(c["eval_set"], dtype=float)}
        for z_id, c in unit["candidates"].items()
    }
    out["eval_keep"] = np.asarray(unit["eval_keep"], dtype=float)
    return out


def _rebuild_arm_distinctness_pairs(pairs: list) -> list:
    """JSON has no int object keys and no tuples: `(duty_map_at_te,
    duty_map_before_leave)` -- each a `dict[int, int]` -- round-trips as
    `[{"0": 3, ...}, {"0": 3, ...}]`. Reverses both so
    `arm_distinctness_check`'s dict `!=` comparison sees the exact int-keyed
    duty maps `run_topology_audit` built, not an artifact of JSON's key
    coercion."""
    return [
        ({int(k): v for k, v in at_te.items()},
         {int(k): v for k, v in before_leave.items()})
        for at_te, before_leave in pairs
    ]


def _reconstruct_topology_result(unit: dict) -> dict:
    """Inverts `audit.topology_unit_for_serialization`: the exact subset of
    keys `assemble_audit_result` reads, with numpy arrays and duty-map int
    keys rebuilt."""
    return {
        "qualifying_calibration_episodes": unit["qualifying_calibration_episodes"],
        "qualifying_audit_episodes": unit["qualifying_audit_episodes"],
        "invalidated_pairs": unit["invalidated_pairs"],
        "arm_distinctness_pairs": _rebuild_arm_distinctness_pairs(unit["arm_distinctness_pairs"]),
        "calibration_units_stable": [_rebuild_unit_arrays(u) for u in unit["calibration_units_stable"]],
        "calibration_units_flex": [_rebuild_unit_arrays(u) for u in unit["calibration_units_flex"]],
        "calibration_units_d_a": [_rebuild_unit_arrays(u) for u in unit["calibration_units_d_a"]],
        "audit_units_stable": [_rebuild_unit_arrays(u) for u in unit["audit_units_stable"]],
        "audit_units_flex": [_rebuild_unit_arrays(u) for u in unit["audit_units_flex"]],
        # R3 section E provenance. Plain JSON scalars, so nothing to rebuild --
        # but it must be carried, or the pooled artifact loses the record of
        # which worlds its numbers were measured in. `.get` with a default keeps
        # a pre-R3 shard poolable instead of crashing; such a shard simply
        # reports no seed-controlled episodes.
        "episode_worlds": unit.get("episode_worlds", []),
    }


def _assert_identity(shards: list[dict], paths: list[str], *, allow_smoke: bool,
                      allow_any_seeds: bool) -> None:
    """Every check SystemExits on violation -- pooling never warns and
    proceeds. Order: contract identity, smoke-flag gate, seed disjointness,
    seed-union membership in a frozen set."""
    ref_path, ref = paths[0], shards[0]
    for p, s in zip(paths[1:], shards[1:]):
        for f in CONTRACT_IDENTITY_FIELDS:
            if s.get(f) != ref.get(f):
                raise SystemExit(
                    f"identity mismatch on '{f}': {ref_path} has {ref.get(f)!r}, "
                    f"{p} has {s.get(f)!r}. These shards do not measure the same "
                    "audit contract.")

    smoke_shards = [p for p, s in zip(paths, shards) if s.get("smoke")]
    if smoke_shards and not allow_smoke:
        raise SystemExit(
            "refusing to pool smoke shard(s) " + ", ".join(smoke_shards) +
            " (SMOKE_NOT_A_RESULT) -- pass --allow-smoke to pool smoke output "
            "for testing only; it is never a scientific result.")
    if len({bool(s.get("smoke")) for s in shards}) > 1:
        raise SystemExit(
            "smoke-flag mismatch across shards: shards must be uniformly "
            "smoke or uniformly real, never a mix.")

    seed_sets = [set(s["topology_seeds"]) for s in shards]
    for i in range(len(shards)):
        for j in range(i + 1, len(shards)):
            overlap = seed_sets[i] & seed_sets[j]
            if overlap:
                raise SystemExit(
                    f"topology seed overlap between {paths[i]} and {paths[j]}: "
                    f"{sorted(overlap)}. Shards must partition topology seeds, "
                    "never share one.")

    union = set().union(*seed_sets)
    if not allow_any_seeds and union not in FROZEN_SEED_SETS:
        initial = sorted(audit.TOPOLOGY_SEEDS_INITIAL)
        expanded = sorted(set(audit.TOPOLOGY_SEEDS_INITIAL) | set(audit.TOPOLOGY_SEEDS_EXPANSION))
        raise SystemExit(
            f"pooled topology-seed union {sorted(union)} matches neither frozen "
            f"set (initial {initial} or expanded {expanded}). Pass "
            "--allow-any-seeds for development pooling of a non-frozen set.")


def pool(shards: list[dict], *, paths: list[str] | None = None, allow_smoke: bool = False,
         allow_any_seeds: bool = False) -> dict:
    """Pools shard result dicts (Task A's `main()` JSON shape) into the same
    shape a monolithic run over the union of their topology seeds would have
    written. Raises SystemExit on any identity violation. Deterministic:
    reconstructs `topology_results` in ascending topology-seed order
    regardless of the order `shards`/`paths` are given in (see module
    docstring, item 2)."""
    if len(shards) < 2:
        raise SystemExit("pooling needs at least two shards")
    paths = paths if paths is not None else [f"<shard {i}>" for i in range(len(shards))]

    _assert_identity(shards, paths, allow_smoke=allow_smoke, allow_any_seeds=allow_any_seeds)

    # One row per topology this shard actually produced units for -- a
    # topology that failed the pinned-coordinate hash assert contributes no
    # unit here, only a `topology_hash_failures` entry (pooled separately).
    rows = []
    for p, s in zip(paths, shards):
        cols = (s["topology_records"], s["calibration_reports"], s["audit_reports"],
                 s["audit_events"], s["topology_units"])
        if len({len(c) for c in cols}) != 1:
            raise SystemExit(
                f"{p}: topology_records/calibration_reports/audit_reports/"
                "audit_events/topology_units have mismatched lengths -- shard "
                "JSON is internally inconsistent.")
        for record, calib_report, audit_report, events, unit in zip(*cols):
            rows.append((int(unit["topology_seed"]), record, calib_report, audit_report,
                         events, unit))
    rows.sort(key=lambda row: row[0])

    topology_records = [r[1] for r in rows]
    calibration_reports = [r[2] for r in rows]
    audit_reports = [r[3] for r in rows]
    audit_events = [r[4] for r in rows]
    topology_units = [r[5] for r in rows]
    topology_results = [_reconstruct_topology_result(u) for u in topology_units]

    topology_hash_failures = sorted(
        (f for s in shards for f in s.get("topology_hash_failures", [])),
        key=lambda f: f["topology_seed"])

    out = audit.assemble_audit_result(topology_results, topology_hash_failures)

    union_seeds = sorted(set().union(*(set(s["topology_seeds"]) for s in shards)))
    result = {
        "contract": shards[0]["contract"],
        "contract_id": shards[0]["contract_id"],
        "procedure_version": shards[0]["procedure_version"],
        "topology_seeds": union_seeds,
        "smoke": bool(shards[0]["smoke"]),
        "note": shards[0]["note"],
        "topology_records": topology_records,
        "calibration_reports": calibration_reports,
        "audit_reports": audit_reports,
        "audit_events": audit_events,
        "topology_units": topology_units,
        "topology_hash_failures": topology_hash_failures,
        "pooling_provenance": {
            "shards": [
                {"path": p, "topology_seeds": sorted(s["topology_seeds"])}
                for p, s in zip(paths, shards)
            ],
        },
    }
    result.update(out)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards", nargs="+", required=True,
                        help="paths to the per-topology-shard d7_s_event_aligned.json files")
    parser.add_argument("--out", default="",
                        help="directory for the pooled d7_s_event_aligned.json")
    parser.add_argument("--allow-smoke", action="store_true",
                         help="permit pooling SMOKE_NOT_A_RESULT shards, for testing only.")
    parser.add_argument("--allow-any-seeds", action="store_true",
                         help="permit a topology-seed union outside the two frozen sets, "
                              "for development pooling only.")
    args = parser.parse_args()

    shards = []
    for p in args.shards:
        with open(p, encoding="utf-8") as h:
            shards.append(json.load(h))

    result = pool(shards, paths=list(args.shards), allow_smoke=args.allow_smoke,
                  allow_any_seeds=args.allow_any_seeds)
    print(f"D7_S_EVENT_ALIGNED_BRANCH={result.get('branch')}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=audit._json_default))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "d7_s_event_aligned.json").open("w", encoding="utf-8") as h:
            json.dump(result, h, ensure_ascii=False, indent=2, default=audit._json_default)


if __name__ == "__main__":
    main()
