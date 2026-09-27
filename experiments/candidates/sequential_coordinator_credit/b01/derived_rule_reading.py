"""Derived paired statistics of a first-cell run, for readers without the gitignored ``regret.npz``.

Writes ``<run root>/first-cell/derived_rule_reading.json`` from ``first-cell/summary.json`` and
``first-cell/regret.npz``: J*, per-arm regret / final J / label statistics, every paired per-seed
difference between arms (regret and final J), the raw / native / per-agent gradient readings with
their paired differences against E1, and the mechanical verdicts of the pre-written Rules 1-3 as
they were declared (Rule 3's reading clause: native calibration, snapshots 40 or 200, both entropy
settings at the same snapshot).  Paired means use the common seeds (contexts and noise are shared
per seed); ``se`` = std(ddof=1) / sqrt(n).  Floats are rounded to seven significant digits.

Usage: ``python -m experiments.candidates.sequential_coordinator_credit.b01.derived_rule_reading <run root>``
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

PRODUCER = "experiments/candidates/sequential_coordinator_credit/b01/derived_rule_reading.py"
READINGS = ("raw", "native", "per_agent")
METRICS = ("cosine", "projection", "variance")
LABEL_KEYS = ("relay_fraction", "greedy_optimal_fraction", "greedy_optimal_mass")


def _r(x):
    return None if x is None else float(f"{x:.7g}")


def mse(values) -> dict:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    n = int(x.size)
    mean = float(x.mean()) if n else None
    se = float(x.std(ddof=1) / np.sqrt(n)) if n > 1 else None
    z = mean / se if (mean is not None and se) else None
    return {"mean": _r(mean), "se": _r(se), "n": n, "z": _r(z)}


def _neg(stat: dict) -> dict:
    return {"mean": None if stat["mean"] is None else -stat["mean"], "se": stat["se"], "n": stat["n"],
            "z": None if stat["z"] is None else -stat["z"]}


def derive(run: Path) -> dict:
    root = run / "first-cell"
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    Z = np.load(root / "regret.npz")
    arms = list(summary["array_axes"]["arms"])
    entropies = list(summary["array_axes"]["entropy"])
    configurations = list(summary["array_axes"]["configurations"])
    snapshots = [int(s) for s in Z["snapshots"]]
    A = {a: i for i, a in enumerate(arms)}
    E = {e: i for i, e in enumerate(entropies)}
    C = {c: i for i, c in enumerate(configurations)}
    pairs = [(x, y) for i, x in enumerate(arms) for y in arms[i + 1:]]

    def reading(which: str, metric: str) -> np.ndarray:
        return Z[f"reading__{which}__{metric}"]

    out = {
        "source": {
            "run": run.name, "regret_npz_sha256": summary["artifacts"].get("regret.npz"),
            "summary_status": summary["status"], "seeds": len(summary["seeds"]), "updates": summary["updates"],
            "producer": PRODUCER,
            "axes": {"training": "[configuration, arm, entropy, seed]",
                     "reading": "[configuration, entropy, snapshot, arm, seed]"},
            "note": "paired = per-seed differences on common seeds; se = std(ddof=1)/sqrt(n); "
                    "projection = <g_est, grad J> / |grad J|^2; variance = full per-sample variance "
                    "in the calibration's units (see readings.py)",
        },
        "arms": arms, "entropy": entropies, "configurations": summary["configurations"], "snapshots": snapshots,
        "J_star": {c: mse(Z["J_star"][C[c]]) for c in configurations},
        "regret": {}, "final_J": {}, "paired_regret": {}, "paired_final_J": {}, "label_statistics": {},
        "readings": {}, "paired_readings_vs_E1": {}, "rules": {},
    }
    for c in configurations:
        for e in entropies:
            k = f"{c}/{e}"
            out["regret"][k] = {a: mse(Z["regret"][C[c], A[a], E[e]]) for a in arms}
            out["final_J"][k] = {a: mse(Z["final_J"][C[c], A[a], E[e]]) for a in arms}
            out["paired_regret"][k] = {
                f"{x}-{y}": mse(Z["regret"][C[c], A[x], E[e]] - Z["regret"][C[c], A[y], E[e]]) for x, y in pairs}
            out["paired_final_J"][k] = {
                f"{x}-{y}": mse(Z["final_J"][C[c], A[x], E[e]] - Z["final_J"][C[c], A[y], E[e]]) for x, y in pairs}
            out["label_statistics"][k] = {
                key: {a: mse(Z[key][C[c], A[a], E[e]]) for a in arms} for key in LABEL_KEYS if key in Z.files}
            out["readings"][k] = {}
            out["paired_readings_vs_E1"][k] = {}
            for t, snap in enumerate(snapshots):
                block = {
                    which: {a: {m: mse(reading(which, m)[C[c], E[e], t, A[a]]) for m in METRICS} for a in arms}
                    for which in READINGS}
                if "reading__raw__cosine_se" in Z.files and "E3" in A:
                    block["E3_jackknife_se_seed_mean"] = {
                        m: _r(float(np.nanmean(reading("raw", f"{m}_se")[C[c], E[e], t, A["E3"]])))
                        for m in ("cosine", "projection")}
                out["readings"][k][f"update_{snap}"] = block
                out["paired_readings_vs_E1"][k][f"update_{snap}"] = {
                    which: {a: {m: mse(reading(which, m)[C[c], E[e], t, A[a]] - reading(which, m)[C[c], E[e], t, A["E1"]])
                                for m in METRICS} for a in arms if a != "E1"}
                    for which in READINGS}

    def paired(k: str, x: str, y: str) -> dict:
        d = out["paired_regret"][k]
        return d[f"{x}-{y}"] if f"{x}-{y}" in d else _neg(d[f"{y}-{x}"])

    corner = configurations[0]
    rule1 = {e: {"E4_minus_E3": paired(f"{corner}/{e}", "E4", "E3")} for e in entropies}
    branch_a = all(v["E4_minus_E3"]["mean"] < 0 and abs(v["E4_minus_E3"]["mean"]) >= 2 * v["E4_minus_E3"]["se"]
                   for v in rule1.values())
    out["rules"]["rule1"] = {"configuration": corner, "per_entropy": rule1,
                             "branch": "a (D wins its best case)" if branch_a else "b (D does not beat E3)"}
    ceiling, rule2 = True, {}
    for e in entropies:
        rule2[e] = {}
        for a in arms:
            if a == "E3*":
                continue
            v = paired(f"{corner}/{e}", a, "E3*")
            within = abs(v["mean"]) < 2 * v["se"]
            ceiling &= within
            rule2[e][f"{a}-E3*"] = {**v, "within_2se": within}
    out["rules"]["rule2"] = {"configuration": corner, "per_entropy": rule2, "ceiling": ceiling}
    chosen = "E4" if branch_a else "E3"
    rule3 = {"chosen_arm": chosen, "per_configuration": {}}
    met_any = False
    for c in configurations:
        regret_clause, regret_ok = {}, True
        for e in entropies:
            v = paired(f"{c}/{e}", chosen, "E1")
            ok = v["mean"] < 0 and abs(v["mean"]) >= 2 * v["se"]
            regret_ok &= ok
            regret_clause[e] = {**v, "ok": ok}
        reading_clause, reading_any = {}, False
        for snap in snapshots:
            if snap not in (40, 200):
                continue
            both, per = True, {}
            for e in entropies:
                d = out["paired_readings_vs_E1"][f"{c}/{e}"][f"update_{snap}"]["native"][chosen]
                cos_ok = d["cosine"]["mean"] >= -2 * d["cosine"]["se"]
                var_ok = d["variance"]["mean"] < 0 and abs(d["variance"]["mean"]) >= 2 * d["variance"]["se"]
                both &= cos_ok and var_ok
                per[e] = {"delta_cosine_native": d["cosine"], "cosine_ok": cos_ok,
                          "delta_variance_native": d["variance"], "variance_ok": var_ok}
            reading_clause[f"update_{snap}"] = {"per_entropy": per, "met_in_both_entropy_settings": both}
            reading_any |= both
        met = regret_ok and reading_any
        met_any |= met
        rule3["per_configuration"][c] = {"regret_clause": regret_clause, "regret_clause_met": regret_ok,
                                         "reading_clause": reading_clause, "reading_clause_met": reading_any,
                                         "C1_met": met}
    rule3["C1_met_at_any_configuration"] = met_any
    out["rules"]["rule3"] = rule3
    return out


def main(argv: list[str]) -> int:
    run = Path(argv[1]).resolve()
    out = derive(run)
    path = run / "first-cell" / "derived_rule_reading.json"
    path.write_text(json.dumps(out, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps({"written": str(path), "bytes": path.stat().st_size, "sha256": digest,
                      "rule1": out["rules"]["rule1"]["branch"], "rule2_ceiling": out["rules"]["rule2"]["ceiling"],
                      "C1_met": out["rules"]["rule3"]["C1_met_at_any_configuration"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
