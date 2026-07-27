"""D7.S prelaunch wall-clock upper bound under the R2 shared-prefix contract.

`EVIDENCE_COMPLEXITY_POLICY.md` requires a zero-compute upper bound before a
conclusion-bearing run may launch, and the R2 contract (section 12) makes the
D7.S audit non-executable until that bound is at most eight hours at the
registered sharding width. This script IS that bound: it is pure arithmetic
over the frozen constants, so it runs in milliseconds, is re-runnable when a
measured step rate lands, and leaves the gate decision auditable instead of
hand-computed in a commit message.

It decides nothing scientific. It reports steps, wall clock and the verdict
string the policy defines.

Usage:
    python scripts/d7_s_prelaunch_cost_bound.py
    python scripts/d7_s_prelaunch_cost_bound.py --s-per-step 0.17
    python scripts/d7_s_prelaunch_cost_bound.py --legal-set-size 8 --s-per-step 0.12
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- frozen constants, R2 contract ------------------------------------------
N_TOPOLOGIES = 8
N_CALIBRATION_EPISODES = 8
N_AUDIT_EPISODES = 8
N_SELECT = 2
N_EVAL = 2
H_STABLE = 139
H_FLEX = 550
T_E_MAX = 950                 # section 2 eligibility deadline; prefix upper bound
SHARD_WIDTH = 8               # one topology per shard
CAP_HOURS = 8.0               # EVIDENCE_COMPLEXITY_POLICY formal cap

# Calibration runs three schedules on the stable limb (constructive_mixed,
# null, full_sync_SET) and two on the flex limb.
CALIBRATION_STABLE_SCHEDULES = 3
CALIBRATION_FLEX_SCHEDULES = 2

# Bootstrap/pooling: 10,000 iterations of small-array numpy over at most a few
# hundred events. Bounded generously -- it is minutes, not hours, and is not
# the term that decides this gate.
POOLING_BOOTSTRAP_ALLOWANCE_S = 900.0


def steps_per_audit_event(*, legal_set_size: int, n_select: int = N_SELECT,
                           n_eval: int = N_EVAL) -> dict:
    """Continuation steps for one qualifying audit event, both limbs.

    Per limb: `n_eval` KEEP continuations, plus `n_select + n_eval` per legal
    candidate. R2 raised this from 2(2+3|Z|) at 1/2 to 2(2+4|Z|) at 2/2."""
    per_limb_continuations = n_eval + legal_set_size * (n_select + n_eval)
    stable = per_limb_continuations * H_STABLE
    flex = per_limb_continuations * H_FLEX
    return {
        "continuations_per_limb": per_limb_continuations,
        "stable_steps": stable,
        "flex_steps": flex,
        "continuation_steps": stable + flex,
    }


def steps_per_calibration_episode() -> int:
    return (CALIBRATION_STABLE_SCHEDULES * H_STABLE
            + CALIBRATION_FLEX_SCHEDULES * H_FLEX)


def bound(*, legal_set_size: int, s_per_step: float, n_select: int = N_SELECT,
          n_eval: int = N_EVAL, shared_prefix: bool = True) -> dict:
    """Upper bound at the registered sharding width.

    Every episode pays `T_E_MAX` for event search (the initial rollout that
    finds `t_e`). Under the shared-prefix realization it pays `T_E_MAX` once
    more for the single canonical replay; under the superseded route it paid
    one replay PER continuation, which is the term the amendment removes.

    `T_E_MAX` is the eligibility deadline, not the typical `t_e`, so both
    prefix terms are deliberately conservative."""
    audit = steps_per_audit_event(legal_set_size=legal_set_size,
                                   n_select=n_select, n_eval=n_eval)
    calib_cont = steps_per_calibration_episode()

    if shared_prefix:
        calib_prefix = 2 * T_E_MAX                     # search + one canonical replay
        audit_prefix = 2 * T_E_MAX
    else:
        n_calib_cont = CALIBRATION_STABLE_SCHEDULES + CALIBRATION_FLEX_SCHEDULES
        calib_prefix = T_E_MAX + n_calib_cont * T_E_MAX
        audit_prefix = T_E_MAX + 2 * audit["continuations_per_limb"] * T_E_MAX

    calib_total = N_CALIBRATION_EPISODES * (calib_prefix + calib_cont)
    audit_total = N_AUDIT_EPISODES * (audit_prefix + audit["continuation_steps"])
    per_topology_steps = calib_total + audit_total

    # One topology per shard, torch_threads=1, so wall clock is one shard.
    wall_s = per_topology_steps * s_per_step + POOLING_BOOTSTRAP_ALLOWANCE_S
    wall_h = wall_s / 3600.0

    return {
        "legal_set_size": legal_set_size,
        "n_select": n_select,
        "n_eval": n_eval,
        "shared_prefix": shared_prefix,
        "s_per_step": s_per_step,
        "continuations_per_limb": audit["continuations_per_limb"],
        "steps_per_audit_event": audit_prefix + audit["continuation_steps"],
        "per_topology_steps": per_topology_steps,
        "total_steps_all_shards": per_topology_steps * N_TOPOLOGIES,
        "shard_width": SHARD_WIDTH,
        "wall_hours": wall_h,
        "within_cap": wall_h <= CAP_HOURS,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legal-set-size", type=int, default=None,
                    help="single |Z| to evaluate; default sweeps the observed 3-8 range")
    ap.add_argument("--s-per-step", type=float, default=None,
                    help="measured seconds per step; default sweeps the recorded 0.10-0.30 band")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    z_values = [args.legal_set_size] if args.legal_set_size else [3, 5, 8]
    rates = [args.s_per_step] if args.s_per_step else [0.10, 0.17, 0.30]

    rows = [bound(legal_set_size=z, s_per_step=r) for z in z_values for r in rates]

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    print("D7.S prelaunch cost bound -- R2 shared-prefix, n_select=2, n_eval=2")
    print(f"cap={CAP_HOURS:.0f}h at {SHARD_WIDTH}-way sharding "
          f"({N_TOPOLOGIES} topologies x [{N_CALIBRATION_EPISODES} calibration "
          f"+ {N_AUDIT_EPISODES} audit] episodes)")
    print()
    print(f"{'|Z|':>4} {'s/step':>7} {'steps/topology':>15} {'wall (h)':>9}  verdict")
    for r in rows:
        verdict = "within cap" if r["within_cap"] else "OVER CAP"
        print(f"{r['legal_set_size']:>4} {r['s_per_step']:>7.2f} "
              f"{r['per_topology_steps']:>15,} {r['wall_hours']:>9.2f}  {verdict}")

    print()
    worst = max(rows, key=lambda r: r["wall_hours"])
    best = min(rows, key=lambda r: r["wall_hours"])
    print(f"upper bound over the swept band: {worst['wall_hours']:.2f} h "
          f"(|Z|={worst['legal_set_size']}, {worst['s_per_step']:.2f} s/step)")
    print(f"lower end of the swept band:     {best['wall_hours']:.2f} h "
          f"(|Z|={best['legal_set_size']}, {best['s_per_step']:.2f} s/step)")

    if not all(r["within_cap"] for r in rows):
        print()
        print("NOT ESTABLISHED: the conservative bound exceeds the cap somewhere in the")
        print("swept band, so the existing 0.10-0.30 s/step record cannot decide this")
        print("gate. R2 section 12 permits ONE microbenchmark of at most twenty minutes")
        print("to pin the shared-prefix continuation rate; rerun with --s-per-step.")


if __name__ == "__main__":
    main()
