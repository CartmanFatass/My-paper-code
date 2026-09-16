#!/usr/bin/env python3
"""ACVC_MATCHED_PACKAGE_COMPARISON_B01: one fresh matched block, one C fit and one M fit, six final panels.

Fixed by em:acvc:convergence (2026-09-16 02:48Z, A with corrections) under Portfolio grant G3. The accepted
comparison runner (C arm: fit, snapshot, C / F / dwell panels) and the accepted transfer runner (M arm: fit,
snapshot, M / F(M) / dwell(M) panels), their evaluators, the protocol, both recipes, the pinned on-policy
dependency and the Binding law are reused by reference and unchanged. This entry binds only the block
identity (MASTER 28731 / evaluation namespace 38731, object and card names, the ordinary plans as metadata)
before any recipe module is imported and before the admitted seed is parsed, then delegates one arm per
process invocation:

  --arm C : bind the protocol identities (C's recipe imports them by value) and delegate to the comparison
            runner's C arm. The transfer runner's binder is never applied on this route.
  --arm M : bind the transfer runner's module globals (its own bind_object carries them to the protocol,
            replaces ARMS/PLANS and the M execution callback) and delegate to it.
  --mode reduce --c-summary --m-summary : the paired publication over the two summaries: sole primary
            P = mean64[J(F(C)) - J(F(M))] and exactly the six supporting contrasts, INCOMPLETE per dependency.

No recipe constant, rate, exposure, panel law or path is altered; ordinary wall plans are not caps; exactly
two originals; no retry, third fit, extra panel or successor.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_acvc_cluster_mappo_comparison_b01 as b01
import run_acvc_m_deployment_transfer_b01 as t
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import protocol as p

OBJECT = "ACVC_MATCHED_PACKAGE_COMPARISON_B01"
CARD = "docs/research/candidates/acvc/ACVC_MATCHED_PACKAGE_COMPARISON_B01_PROSPECTIVE_CARD_20260915.md"
MASTER, EVALUATION_NAMESPACE = 28731, 38731
PLANS = {"C": 2600, "M": 1200}  # Portfolio G3 initial planning judgments; plans, not caps
PRIOR_IDENTITIES = ((28331, 38331), (28431, 38431), (28531, 38531), (28631, 38631), (8961, 8962))
TRANSFER_IDENTITIES = ((28531, 38531), (MASTER, EVALUATION_NAMESPACE))
MEI_J = .01
FROZEN = ("UPSTREAM_SHA", "TRAIN_EPISODES", "EVAL_EPISODES", "HORIZON")  # asserted by the tests
# Scientific panel -> (input summary arm, existing panel key). Constructor offsets 62/63/64 and 65/66/67.
PANEL_SOURCES = {"C": ("C", "C"), "F(C)": ("C", "F"), "own-dwell(C)": ("C", "dwell"),
                 "M": ("M", "M"), "F(M)": ("M", "F(M)"), "own-dwell(M)": ("M", "dwell(M)")}
PRIMARY = ("F(C)", "F(M)")
SUPPORTS = {"C-M": ("C", "M"), "F(C)-C": ("F(C)", "C"), "F(M)-M": ("F(M)", "M"),
            "F(C)-own-dwell(C)": ("F(C)", "own-dwell(C)"), "F(M)-own-dwell(M)": ("F(M)", "own-dwell(M)"),
            "own-dwell(C)-own-dwell(M)": ("own-dwell(C)", "own-dwell(M)")}
PRIMARY_LABELS = {"UP": "F_C_ABOVE_MEI", "DOWN": "F_M_ABOVE_MEI", "WITHIN_MEI": "WITHIN_MEI", "INCOMPLETE": "INCOMPLETE"}


def _refuse_early_import():
    for name in ("mappo", "c_fit"):
        if f"experiments.candidates.acvc.cluster_mappo_comparison_b01.{name}" in sys.modules:
            raise RuntimeError(f"{name} was imported before the block identities were bound")


def bind_c():
    """C route: the protocol identities and plans; ARMS['C'] stays ('C', 'F', 'dwell'); no transfer binder."""
    _refuse_early_import()
    p.MASTER, p.EVALUATION_NAMESPACE, p.OBJECT, p.CARD = MASTER, EVALUATION_NAMESPACE, OBJECT, CARD
    p.PLANS = dict(PLANS)


def bind_m():
    """M route: the transfer runner's module globals; its bind_object carries them to the protocol."""
    _refuse_early_import()
    if (t.MASTER, t.EVALUATION_NAMESPACE) not in TRANSFER_IDENTITIES:
        raise RuntimeError("the B01 transfer runner carries unexpected identities")
    t.OBJECT, t.CARD = OBJECT, CARD
    t.MASTER, t.EVALUATION_NAMESPACE = MASTER, EVALUATION_NAMESPACE
    t.ORDINARY_PLAN_SECONDS = PLANS["M"]


def _scores(summary, fitted_arm, key):
    """A complete finite 64-score panel of an eligible fit under the bound identities, else None."""
    if not summary or not p.fit_eligible(summary, fitted_arm):
        return None
    raw = summary.get("panels", {}).get(key, {})
    scores = raw.get("scores_J")
    ok = (raw.get("complete") is True and isinstance(scores, list) and len(scores) == p.EVAL_EPISODES
          and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in scores))
    return list(scores) if ok else None


def reduce_matched(c_summary, m_summary):
    """Paired publication: P (sole primary) and exactly the six supports; INCOMPLETE per dependency."""
    bind_c()  # the summaries are compared against the bound identities, never against the protocol defaults
    summaries = {"C": c_summary, "M": m_summary}
    eligible = {arm: bool(s) and p.fit_eligible(s, arm) for arm, s in summaries.items()}
    values, panels = {}, {}
    for name, (arm, key) in PANEL_SOURCES.items():
        raw = (summaries[arm] or {}).get("panels", {}).get(key, {}) if summaries[arm] else {}
        values[name] = _scores(summaries[arm], arm, key)
        panels[name] = dict(raw, source_arm=arm, source_key=key,
                            eligible_for_bound_comparison=values[name] is not None)
    primary = p.contrast(values[PRIMARY[0]], values[PRIMARY[1]])
    primary = dict(primary, reading=PRIMARY_LABELS[primary["reading"]], left=PRIMARY[0], right=PRIMARY[1])
    supports = {}
    for name, (left, right) in SUPPORTS.items():
        supports[name] = dict(p.contrast(values[left], values[right]), left=left, right=right)
    identity = None
    if all(values[k] is not None for k in ("C", "F(C)", "M", "F(M)")):
        fc, c, m, fm = (np.asarray(values[k], dtype=np.float64) for k in ("F(C)", "C", "M", "F(M)"))
        residual = (fc - fm) - ((fc - c) + (c - m) - (fm - m))
        identity = dict(rowwise="p_e = [F(C)-C]_e + [C-M]_e - [F(M)-M]_e (arithmetic, not attribution)",
                        max_abs_residual_J=float(np.max(np.abs(residual))))
    interventions = {arm: (s or {}).get("interventions") for arm, s in summaries.items()}
    return dict(object=OBJECT, card=CARD, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE,
                complete=primary["complete"], eligible_fits=eligible, panels=panels,
                primary="P", primary_definition="mean64[J(F(C)) - J(F(M))] on the common final worlds",
                P=primary, supports=supports, decomposition_identity=identity, MEI_J=MEI_J,
                interventions=interventions, training_instances=2, plans_seconds=dict(PLANS), plan_is_cap=False,
                claim_ceiling="One fresh prospectively paired block with one attained C policy and one attained M "
                              "policy on common final worlds; conditional-world SD/SE only; P is the sole primary, "
                              "the six supports are not co-primary; no pooling with earlier objects.")


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def main(argv=None):
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["run", "reduce"], default="run")
    parser.add_argument("--arm", choices=["C", "M"])
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha")
    parser.add_argument("--on-policy-root", type=Path)
    parser.add_argument("--c-summary", type=Path)
    parser.add_argument("--m-summary", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "reduce":
        args.output.mkdir(parents=True, exist_ok=True)
        result = reduce_matched(_read(args.c_summary), _read(args.m_summary))
        (args.output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                                                  encoding="utf-8")
        return 0
    if args.arm is None or not args.launch_sha:
        parser.error("run needs --arm C|M and --launch-sha")
    if args.arm == "C":
        bind_c()
        return b01.main(["--arm", "C", "--seed", str(MASTER), "--output", str(args.output),
                         "--launch-sha", args.launch_sha])
    if not args.on_policy_root:
        parser.error("the M arm needs --on-policy-root")
    bind_m()  # before the transfer runner parses: its parser admits only the bound seed
    return t.main(["--seed", str(MASTER), "--output", str(args.output), "--launch-sha", args.launch_sha,
                   "--on-policy-root", str(args.on_policy_root)])


if __name__ == "__main__":
    raise SystemExit(main())
