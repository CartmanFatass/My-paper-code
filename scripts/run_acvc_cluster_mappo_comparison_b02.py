#!/usr/bin/env python3
"""One further unchanged C/M paired block (em:acvc:convergence decision 2026-09-15, option A, k = 1).

The frozen B01 runner, protocol, C recipe, pinned on-policy dependency and action adapter are reused by
reference; only the block identities change. Fresh master 28431 and evaluation namespace 38431 replace
28331/38331 before any recipe module is imported, so every derived seed, reset world, generator and
checkpoint label belongs to the new block. No recipe constant, rate, exposure, panel law or path is
altered. Ordinary wall plans are not caps; no retry, extra fit or successor.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_acvc_cluster_mappo_comparison_b01 as b01
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import protocol as p

OBJECT = "ACVC_CLUSTER_MAPPO_COMPARISON_B02"
CARD = "docs/research/candidates/acvc/pro_packets/20260915_cluster_mappo_comparison_b01_result_review/INTAKE.md"
MASTER, EVALUATION_NAMESPACE = 28431, 38431
FROZEN = ("UPSTREAM_SHA", "TRAIN_EPISODES", "EVAL_EPISODES", "HORIZON", "ARMS", "PLANS")  # asserted by the tests


def bind_block():
    """Rebind the protocol identities in place; recipe modules import them only after this call."""
    for name in ("mappo", "c_fit"):
        if f"experiments.candidates.acvc.cluster_mappo_comparison_b01.{name}" in sys.modules:
            raise RuntimeError(f"{name} was imported before the block identities were bound")
    p.MASTER, p.EVALUATION_NAMESPACE, p.OBJECT, p.CARD = MASTER, EVALUATION_NAMESPACE, OBJECT, CARD


def main(argv=None):
    bind_block()
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--seed" in argv:
        index = argv.index("--seed")
        if argv[index + 1:index + 2] != [str(MASTER)]:
            raise SystemExit(f"--seed must be {MASTER} for block 2")
    return b01.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
