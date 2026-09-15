#!/usr/bin/env python3
"""ACVC_M_DEPLOYMENT_TRANSFER_B02: one further independently initialised M fit with the unchanged three panels.

Selected by em:acvc:convergence in its 2026-09-15 result review of B01 (B, PRO_FINAL); the launch waits on
the Portfolio one-fit grant. The B01 transfer runner, wrapped evaluator, reducer, protocol, M recipe, pinned
on-policy dependency and action adapter are reused by reference and unchanged. This entry rebinds only the
object identity on the B01 transfer runner (MASTER 28631 / evaluation namespace 38631, object and card
names, the ordinary plan) before any recipe module is imported, then delegates run and reduce to it, so the
new identities reach initialisation, training resets, action streams, the three final panels and the
reducer through the same bound path B01 used. Nothing is transferred from the B01 fit. No recipe constant,
rate, exposure or panel law is altered; ordinary wall plans are not caps; no retry, second instance or
successor.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_acvc_m_deployment_transfer_b01 as t

OBJECT = "ACVC_M_DEPLOYMENT_TRANSFER_B02"
CARD = "docs/research/candidates/acvc/ACVC_M_DEPLOYMENT_TRANSFER_B02_PROSPECTIVE_CARD_20260915.md"
MASTER, EVALUATION_NAMESPACE = 28631, 38631
ORDINARY_PLAN_SECONDS = 1200  # basis: B01's 985.12 s alone on the node; a plan, not a cap
PRIOR_IDENTITIES = ((28331, 38331), (28431, 38431), (28531, 38531), (8961, 8962))
B01_IDENTITIES = (28531, 38531)


def bind_b02():
    """Rebind the B01 transfer runner's identities in place; its own bind_object carries them to the protocol."""
    for name in ("mappo", "c_fit"):
        if f"experiments.candidates.acvc.cluster_mappo_comparison_b01.{name}" in sys.modules:
            raise RuntimeError(f"{name} was imported before the B02 identities were bound")
    if (t.MASTER, t.EVALUATION_NAMESPACE) not in (B01_IDENTITIES, (MASTER, EVALUATION_NAMESPACE)):
        raise RuntimeError("the B01 transfer runner carries unexpected identities")
    t.OBJECT, t.CARD = OBJECT, CARD
    t.MASTER, t.EVALUATION_NAMESPACE = MASTER, EVALUATION_NAMESPACE
    t.ORDINARY_PLAN_SECONDS = ORDINARY_PLAN_SECONDS


def main(argv=None):
    bind_b02()  # before parsing: the B01 parser admits only the bound seed; reduce binds the protocol after parsing
    return t.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
