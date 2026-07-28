"""Step E — the proof-sized assembled-path exercise, on development topology only.

Contract closure step E: drive every registered R4 outcome through the REAL
`assemble_audit_result`, starting from a topology unit a REAL run produced.

Why this is not the same as the reachability check already done. The
realization-conformance review drove all fifteen limb-state combinations through
the real assembler using hand-built topology results in the shape
`run_topology_audit` returns. That proves the assembler maps states to branches.
It does not prove that the shape a real environment run actually emits, carried
through serialization and the pooler's reconstruction, feeds those branches at
all. This exercise starts from the artifact of a real smoke run on topology
20260725 and reconstructs it with the pooler's own
`_reconstruct_topology_result` -- the production path -- before touching
anything.

What is steered, and what is not. Only the per-topology U* contributions and the
specific structures each precedence branch reads. Every unit's real component
records, arm-distinctness pairs, episode-world provenance and Part-A block come
from the run. The assembler, the bootstrap and the resolvers are untouched.

Steering method: the exercise replicates the one real topology into N identical
copies, so every bootstrap resample sees the same value and the interval collapses
to a point (lcb == ucb == U*). The registered iteration count is therefore
numerically irrelevant here and is left alone. With MATERIALITY_MARGIN = 5.0:

    U* = -10  -> UCB < -5          -> MATERIAL
    U* =   0  -> LCB > -5          -> AFFIRMATIVE_NONMATERIAL
    U* =  -5  -> neither, equality -> UNRESOLVED   (never MATERIAL)

`SMOKE_NOT_A_RESULT`: this reads a smoke artifact and fabricates limb values. It
is an instrument exercise and can never be a source-necessity result. It writes
no artifact into any run directory.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import numpy as np                                 # noqa: E402
import audit_d7_s_event_aligned as audit           # noqa: E402
import pool_d7_s_event_aligned_shards as pooling   # noqa: E402

N_TOPOLOGIES = 8
U_STAR_FOR_STATE = {"MATERIAL": -10.0, "AFFIRMATIVE_NONMATERIAL": 0.0, "UNRESOLVED": -5.0}


def _set_u_star(unit: dict, value: float) -> None:
    """Make this unit's U* equal `value`: V_KEEP = 0, V_SET = value.

    The key is `eval_set`, not `eval`. Reading the wrong one here would be
    invisible rather than loud: `eval_keep` is the arm that is 0.0 on both limbs
    in an unsteered unit, so a guard pointed at it sees no change at all. That
    exact confusion already produced one indistinguishable pooler guard in this
    repository.
    """
    unit["eval_keep"] = np.zeros(len(unit["eval_keep"]), dtype=float)
    for cand in unit["candidates"].values():
        cand["eval_set"] = np.full(len(cand["eval_set"]), float(value))


def _set_invariance(unit: dict, invariant: bool) -> None:
    for pair in unit.get("component_audit", {}).get("pairwise_equality", []):
        pair["sequences_exactly_equal"] = invariant


def _topologies(base: dict, *, stable: str | None, flex: str | None,
                stable_invariant: bool = False, flex_invariant: bool = False,
                drop_component_audit: bool = False, clear_support: bool = True) -> list[dict]:
    """N copies of the real unit, steered.

    `clear_support` raises the qualifying-episode counters to the registered
    minimum. A proof-sized smoke run produces ONE qualifying episode per limb and
    the gate needs MIN_SUPPORT_EPISODES_PER_TOPOLOGY across
    MIN_SUPPORT_TOPOLOGIES, so without this every case lands on branch 2 and the
    exercise proves only that the support gate works. These counters are
    fabricated, and that is exactly why this artifact can never be a result --
    the branch-2 case below leaves them at the real value on purpose, so the gate
    is still shown holding.
    """
    out = []
    for _ in range(N_TOPOLOGIES):
        r = copy.deepcopy(base)
        if clear_support:
            r["qualifying_calibration_episodes"] = audit.MIN_SUPPORT_EPISODES_PER_TOPOLOGY
            r["qualifying_audit_episodes"] = audit.MIN_SUPPORT_EPISODES_PER_TOPOLOGY
        for limb, state, invariant in (("audit_units_stable", stable, stable_invariant),
                                       ("audit_units_flex", flex, flex_invariant)):
            for unit in r[limb]:
                if drop_component_audit:
                    unit.pop("component_audit", None)
                    continue
                _set_invariance(unit, invariant)
                if state is not None:
                    _set_u_star(unit, U_STAR_FOR_STATE[state])
        out.append(r)
    return out


def _run(label: str, topologies: list[dict], hash_failures=None) -> dict:
    result = audit.assemble_audit_result(topologies, hash_failures or [])
    return {
        "case": label,
        "branch": result.get("branch"),
        "branch_reason": result.get("branch_reason"),
        "limb_states": result.get("limb_states"),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: d7s_r4_assembled_path_exercise.py <run-dir-with-stdout.json>",
              file=sys.stderr)
        return 2
    artifact_path = Path(argv[0])
    if artifact_path.is_dir():
        artifact_path = artifact_path / "stdout.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    units = artifact.get("topology_units") or []
    if len(units) != 1:
        print(f"expected exactly one topology unit, found {len(units)}", file=sys.stderr)
        return 2
    seed = units[0].get("topology_seed")
    if seed != audit.TOPOLOGY_SEED_DEV:
        print(f"refusing: unit is topology {seed}, not the development topology "
              f"{audit.TOPOLOGY_SEED_DEV}. Step E is the DEV topology only.", file=sys.stderr)
        return 2

    # The production reconstruction path, not a hand-built shape.
    base = pooling._reconstruct_topology_result(units[0])

    rows = []
    states = ("MATERIAL", "AFFIRMATIVE_NONMATERIAL", "UNRESOLVED")
    for s in states:
        for f in states:
            rows.append(_run(f"{s} / {f}", _topologies(base, stable=s, flex=f)))
    # COMPONENT_INVARIANT on one limb while the other stays material: the two
    # flex-only positives the contract's combined mapping distinguishes.
    rows.append(_run("COMPONENT_INVARIANT / MATERIAL",
                     _topologies(base, stable=None, flex="MATERIAL", stable_invariant=True)))
    rows.append(_run("MATERIAL / COMPONENT_INVARIANT",
                     _topologies(base, stable="MATERIAL", flex=None, flex_invariant=True)))
    # Precedence branches.
    rows.append(_run("branch 1: component audit missing",
                     _topologies(base, stable="MATERIAL", flex="MATERIAL",
                                 drop_component_audit=True)))
    rows.append(_run("branch 1: topology hash failure",
                     _topologies(base, stable="MATERIAL", flex="MATERIAL"),
                     hash_failures=[{"topology_seed": audit.TOPOLOGY_SEED_DEV}]))
    rows.append(_run("branch 2: real qualifying counts, support insufficient",
                     _topologies(base, stable="MATERIAL", flex="MATERIAL", clear_support=False)))
    rows.append(_run("branch 3: both limbs exactly invariant",
                     _topologies(base, stable=None, flex=None,
                                 stable_invariant=True, flex_invariant=True)))

    width = max(len(r["case"]) for r in rows)
    print(f"{'case'.ljust(width)}  branch")
    print("-" * (width + 40))
    for r in rows:
        print(f"{r['case'].ljust(width)}  {r['branch']}"
              + (f"  [{r['branch_reason']}]" if r["branch_reason"] else "")
              + (f"  {r['limb_states']}" if r["limb_states"] else ""))

    observed = {r["branch"] for r in rows}
    expected = set(audit.COMBINED_RESULT_MAP.values()) | {
        "INVALID_EVENT_ALIGNED_AUDIT", "SOURCE_EVENT_SUPPORT_INSUFFICIENT",
        "PRIMARY_G_DEGENERATE"}
    missing = sorted(expected - observed)
    print()
    print(f"distinct outcomes observed: {len(observed)}")
    for b in sorted(observed):
        print(f"  {b}")
    if missing:
        print("\nNOT REACHED through the real assembler from the real unit:", file=sys.stderr)
        for b in missing:
            print(f"  {b}", file=sys.stderr)
        return 1
    print("\nSTEP_E_ASSEMBLED_PATH_OK -- every registered outcome reached from the "
          "real dev-topology unit through the production reconstruction path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
