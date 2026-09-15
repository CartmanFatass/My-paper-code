#!/usr/bin/env python3
"""One fresh M fit of the frozen block-2 recipe with three private final panels M / F(M) / own-dwell(M).

Object ACVC_M_DEPLOYMENT_TRANSFER_B01 (em:acvc:convergence 2026-09-15 20:28Z, B with corrections). The
frozen B01 runner, protocol, M recipe, pinned on-policy dependency and action adapter are reused by
reference exactly as block 2 did; the fresh identities MASTER 28531 / evaluation namespace 38531 are
bound before any recipe module is imported. The only new execution is evaluation: after the unchanged
training and the unchanged single M panel, the saved final snapshot is loaded twice more and evaluated
under the unchanged F (retrace) and own-dwell (zero command) deployment laws through
`m_deployment_transfer_b01.wrapped_eval`. No recipe constant, rate, exposure or panel law is altered;
ordinary wall plans are not caps; no retry, second instance or successor.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_acvc_cluster_mappo_comparison_b01 as b01
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import protocol as p
from experiments.candidates.acvc.m_deployment_transfer_b01.wrapped_eval import PANELS, evaluate_wrapped

OBJECT = "ACVC_M_DEPLOYMENT_TRANSFER_B01"
CARD = "docs/research/candidates/acvc/ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md"
MASTER, EVALUATION_NAMESPACE = 28531, 38531
CONSTRUCTOR_OFFSETS = {"M": 65, "F(M)": 66, "dwell(M)": 67}  # 65 is the B01 runner's own M offset
ORDINARY_PLAN_SECONDS = 2600
MEI_J = .01
FROZEN = ("UPSTREAM_SHA", "TRAIN_EPISODES", "EVAL_EPISODES", "HORIZON")  # asserted by the tests
_B01_EXECUTE_M = b01.execute_m


def bind_object():
    """Rebind the protocol identities and the panel set in place; recipe modules import only after this."""
    for name in ("mappo", "c_fit"):
        if f"experiments.candidates.acvc.cluster_mappo_comparison_b01.{name}" in sys.modules:
            raise RuntimeError(f"{name} was imported before the object identities were bound")
    p.MASTER, p.EVALUATION_NAMESPACE, p.OBJECT, p.CARD = MASTER, EVALUATION_NAMESPACE, OBJECT, CARD
    p.ARMS = {"M": PANELS}
    p.PLANS = {"M": ORDINARY_PLAN_SECONDS}
    b01.execute_m = execute_m_with_panels


def execute_m_with_panels(output, summary, emit, emit_update, progress):
    from experiments.candidates.acvc.cluster_mappo_comparison_b01 import mappo as m

    if (m.MASTER, m.EVALUATION_NAMESPACE) != (p.MASTER, p.EVALUATION_NAMESPACE):
        raise RuntimeError("the M recipe module did not receive the bound identities")
    # Unchanged training, snapshot, first load and the single M panel (constructor offset 65).
    _B01_EXECUTE_M(output, summary, emit, emit_update, progress)
    summary["deployment_laws"] = dict(
        F="native_link_loss_b01.binding.Binding opportunities -> retrace command; else the M proposal",
        dwell="the same opportunities -> zero command; else the M proposal",
        feedback="the actually sent command; remaining hold 0; fresh Binding per episode; one actor draw per tick")
    args, _ = m.configuration()
    counts = summary["counts"]
    checkpoint = m.torch.load(Path(output) / summary["checkpoint"], map_location="cpu", weights_only=True)
    for arm in PANELS[1:]:
        policy, _ = m.make_policy(args)
        policy.actor.load_state_dict(checkpoint["actor"])
        counts["post_fit_loads"] += 1
        env = p.make_cluster(100000 * p.EVALUATION_NAMESPACE + CONSTRUCTOR_OFFSETS[arm])
        counts["environment_constructors"] += 1
        counts["unscored_constructor_resets"] += 1
        for episode in range(p.EVAL_EPISODES):
            evaluate_wrapped(policy, env, episode, counts, emit, arm, p.EVALUATION_NAMESPACE, p.HORIZON)
        progress()
        del policy


def _relabel(contrast, up, down):
    if contrast.get("reading") in ("UP", "DOWN", "WITHIN_MEI"):
        contrast = dict(contrast, reading={"UP": up, "DOWN": down, "WITHIN_MEI": "WITHIN_MEI"}[contrast["reading"]])
    return contrast


def reduce_transfer(summary):
    """Offline readout of one fit's three panels: T_F (primary), T_D and the paired U."""
    eligible = p.fit_eligible(summary, "M") if summary else False
    panels, values = {}, {}
    for arm in PANELS:
        raw = summary.get("panels", {}).get(arm, {}) if summary else {}
        scores = raw.get("scores_J")
        valid = (eligible and raw.get("complete") is True and isinstance(scores, list)
                 and len(scores) == p.EVAL_EPISODES
                 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in scores))
        panels[arm] = dict(raw, eligible_for_bound_comparison=valid)
        values[arm] = scores if valid else None
    contrasts = {
        "T_F": _relabel(p.contrast(values["F(M)"], values["M"]), "TRANSFERS", "ADVERSE"),
        "T_D": p.contrast(values["dwell(M)"], values["M"]),
        "U": p.contrast(values["F(M)"], values["dwell(M)"]),
    }
    return dict(object=OBJECT, card=CARD, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE,
                complete=all(v["complete"] for v in contrasts.values()), eligible_fit=eligible,
                panels=panels, primary="T_F", contrasts=contrasts, MEI_J=MEI_J,
                interventions=(summary or {}).get("interventions"),
                training_instances=1,
                claim_ceiling="One training instance of the conventional proposer with three matched final "
                              "panels; conditional-world SD/SE only; T_F is the sole primary, U is supporting.")


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["run", "reduce"], default="run")
    parser.add_argument("--seed", type=int, choices=[MASTER], default=MASTER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha")
    parser.add_argument("--on-policy-root", type=Path)
    parser.add_argument("--m-summary", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "reduce":
        summary = json.loads(args.m_summary.read_text(encoding="utf-8")) if args.m_summary else None
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(json.dumps(reduce_transfer(summary), indent=2,
                                                            allow_nan=False) + "\n", encoding="utf-8")
        return 0
    if not args.launch_sha or not args.on_policy_root:
        parser.error("run needs --launch-sha and --on-policy-root")
    bind_object()
    return b01.run(args.output, "M", args.launch_sha, args.on_policy_root)


if __name__ == "__main__":
    raise SystemExit(main())
