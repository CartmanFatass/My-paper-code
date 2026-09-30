"""Trainer for the student (coupled_host_planner_distillation, cell b01 piece 3).

Authority: NOTES.md "REVISED PRE-DECLARATION" items 5-6 (commit d62bb0bb1) and the piece-3 L0
scope note (with amendments).  Exposure, fixed before any label exists:

* segment A: ``run_markov`` label-mode output on training worlds 3000-3127 (one sample per T_M
  re-plan, K = 3 layouts of seeds 0/1/2 on the same known map and positions);
* S0 = ``student.make_net()`` (seed 932201); S_bc = S0 trained on A, Adam lr 1e-3, batch 64,
  300 epochs, shuffling seed 932201, no weight decay, no early stopping;
* segment B: ONE DAgger round -- S_bc rolled in on 3000-3063 with T_M's trigger; every student
  decision that ran a forward pass is relabelled with ``B4.plan_on_known`` for seeds 0/1/2 on the
  student's own map and positions (the calls T_M's label mode makes) after the decision's targets
  are fixed; S = S_bc continued on A u B with a FRESH Adam (lr 1e-3) for 150 epochs (same batch
  and shuffling seed).

Deterministic: float32 net, one CPU thread, fixed init and shuffling seeds.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    DEV_WORLDS,
    HOLDOUT_WORLDS,
    N_UAVS,
)
from experiments.candidates.coupled_host_planner_distillation import student as S
from experiments.candidates.coupled_host_replan_timing.rules import PLANNER_BUDGET

torch.set_num_threads(1)

LR = 1e-3
BATCH = 64
SHUFFLE_SEED = S.INIT_SEED
EPOCHS_A = 300
EPOCHS_B = 150
LABEL_SEEDS = (0, 1, 2)
DAGGER_WORLDS = tuple(range(3000, 3064))
PANEL_WORLDS = frozenset(DEV_WORLDS) | frozenset(HOLDOUT_WORLDS)


# ============================================================ data


def load_labelled(run_dir: Path, allow_panels: bool = False) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """(X [N, 168] float64, Y [N, K, 6, 3] metres, meta) from ``<run_dir>/worlds/*.json``.

    Refuses a K that differs across samples, and (unless ``allow_panels``) any dev / hold-out world.
    """
    run_dir = Path(run_dir)
    files = sorted((run_dir / "worlds").glob("*.json"), key=lambda p: int(p.stem))
    if not files:
        raise FileNotFoundError(f"no worlds/*.json under {run_dir}")
    xs, ys, per_world, seeds_seen = [], [], {}, None
    digest = hashlib.sha256()
    for path in files:
        raw = path.read_bytes()
        digest.update(path.name.encode() + b"\0" + hashlib.sha256(raw).digest())
        payload = json.loads(raw)
        world = int(payload["world"])
        if world != int(path.stem):
            raise ValueError(f"{path}: world {world} != file name")
        if world in PANEL_WORLDS and not allow_panels:
            raise ValueError(f"world {world} is a dev / hold-out panel world; it never enters the labels")
        per_world[world] = len(payload["labelled"])
        for lab in payload["labelled"]:
            layouts = np.asarray(lab["layouts"], dtype=np.float64)
            feat = np.asarray(lab["features"], dtype=np.float64)
            if feat.shape != (S.IN_DIM,) or layouts.ndim != 3 or layouts.shape[1:] != (N_UAVS, 3):
                raise ValueError(f"{path}: bad sample shapes {feat.shape} {layouts.shape}")
            if seeds_seen is None:
                seeds_seen = list(lab["seeds"])
            if list(lab["seeds"]) != seeds_seen or layouts.shape[0] != len(seeds_seen):
                raise ValueError(f"{path}: K / seeds differ across samples ({lab['seeds']} vs {seeds_seen})")
            xs.append(feat)
            ys.append(layouts)
    if not xs:
        raise ValueError(f"{run_dir}: no labelled decisions")
    X, Y = np.stack(xs), np.stack(ys)
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(Y))):
        raise ValueError("non-finite samples")
    meta = {"dir": str(run_dir), "worlds": sorted(per_world), "per_world": per_world,
            "n": int(X.shape[0]), "K": int(Y.shape[1]), "seeds": seeds_seen,
            "files_digest_sha256": digest.hexdigest()}
    return X, Y, meta


def load_segment(run_dir: Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Segment data from a ``run_markov`` label-mode run directory; panel worlds refused."""
    return load_labelled(run_dir, allow_panels=False)


def tensors(X: np.ndarray, Y: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
    return (torch.from_numpy(np.asarray(X, dtype=np.float64)).to(S.DTYPE),
            torch.from_numpy(S.normalise(np.asarray(Y, dtype=np.float64))).to(S.DTYPE))


# ============================================================ fit


def dataset_loss(net: S.StudentNet, X: np.ndarray, Y: np.ndarray, k_first: int | None = None,
                 chunk: int = 256) -> dict[str, Any]:
    """Mean per-item loss (no grad); ``k_first`` restricts to the first k layouts (seed 0 = 1)."""
    Xt, Yt = tensors(X, Y)
    if k_first is not None:
        Yt = Yt[:, :k_first]
    net.eval()
    vals = []
    with torch.no_grad():
        for i in range(0, Xt.shape[0], chunk):
            vals.append(S.per_item_loss(net(Xt[i:i + chunk]), Yt[i:i + chunk]))
    v = torch.cat(vals).double().numpy()
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if v.size > 1 else None,
            "median": float(np.median(v)), "n": int(v.size), "K": int(Yt.shape[1])}


def fit(net: S.StudentNet, X: np.ndarray, Y: np.ndarray, epochs: int, lr: float = LR,
        batch: int = BATCH, seed: int = SHUFFLE_SEED, log: Callable[[str], None] | None = None,
        log_every: int = 25) -> dict[str, Any]:
    """Adam (no weight decay), fixed shuffling seed, no early stopping; trains ``net`` in place.

    Returns ``epoch_loss`` (per-epoch sample-weighted mean of the minibatch losses), the full-set
    loss before the first and after the last step, step count and CPU.
    """
    Xt, Yt = tensors(X, Y)
    n = int(Xt.shape[0])
    gen = torch.Generator().manual_seed(int(seed))
    opt = torch.optim.Adam(net.parameters(), lr=float(lr), weight_decay=0.0)
    initial = dataset_loss(net, X, Y)["mean"]
    epoch_loss: list[float] = []
    steps = 0
    c0 = time.process_time()
    for epoch in range(int(epochs)):
        net.train()
        order = torch.randperm(n, generator=gen)
        total = 0.0
        for i in range(0, n, int(batch)):
            idx = order[i:i + int(batch)]
            loss = S.layout_loss(net(Xt[idx]), Yt[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            steps += 1
            total += float(loss.detach()) * int(idx.numel())
        epoch_loss.append(total / n)
        if not np.isfinite(epoch_loss[-1]):
            raise FloatingPointError(f"non-finite loss at epoch {epoch + 1}")
        if log is not None and ((epoch + 1) % log_every == 0 or epoch == 0 or epoch + 1 == epochs):
            log(f"epoch={epoch + 1}/{epochs} loss={epoch_loss[-1]:.6f} cpu={time.process_time() - c0:.1f}s")
    cpu = time.process_time() - c0
    net.eval()
    return {"epoch_loss": epoch_loss, "initial_loss": initial,
            "final_loss": dataset_loss(net, X, Y)["mean"], "epochs": int(epochs), "steps": steps,
            "n": n, "K": int(Yt.shape[1]), "lr": float(lr), "batch": int(batch), "seed": int(seed),
            "optimizer": "Adam(betas=(0.9, 0.999), eps=1e-8, weight_decay=0)", "cpu_s": cpu}


# ============================================================ DAgger


def dagger_round(net_bc: S.StudentNet, worlds: Sequence[int], budget: int = PLANNER_BUDGET,
                 seeds: Sequence[int] = LABEL_SEEDS, horizon: int = S.HORIZON,
                 log: Callable[[str], None] | None = None, out_dir: Path | None = None,
                 verify: bool = True) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Roll in ``net_bc`` on ``worlds``; relabel every forward-pass decision with the K seeds.

    The relabelling runs in the arm's ``label_hook`` after the decision's targets are fixed
    (``B4.plan_on_known`` deep-copies the host).  With ``verify`` every world is re-rolled without
    the hook and the per-decision targets and C_bh series must be identical (no planner call
    influences the roll-in).  Returns (X_B, Y_B [N, K, 6, 3], readings).
    """
    seeds = tuple(int(s) for s in seeds)
    if not seeds or seeds[0] != 0 or len(set(seeds)) != len(seeds):
        raise ValueError("label seeds must be distinct and start with the control seed 0")
    bad = [w for w in worlds if int(w) in PANEL_WORLDS]
    if bad:
        raise ValueError(f"panel worlds {bad} never enter the labels")
    xs, ys, rows = [], [], []
    cpu_label = 0.0
    for world in worlds:
        world = int(world)
        labelled: list[dict[str, Any]] = []
        label_cpu = [0.0]

        def hook(env, xy, positions, pending, _labelled=labelled, _cpu=label_cpu):
            layouts = []
            for seed in seeds:
                c0 = time.process_time()
                relay, _flat = B4.plan_on_known(env, xy, seed, int(budget))
                _cpu[0] += time.process_time() - c0
                layouts.append(np.array(relay.positions_xyz, dtype=float, copy=True).reshape(N_UAVS, 3))
            _labelled.append({"step": pending["step"], "known": pending["known"],
                              "features": pending["features"], "positions": positions,
                              "seeds": list(seeds), "layouts": np.stack(layouts),
                              "student_layout": pending["layout"]})

        c0 = time.process_time()
        ep = S.run_student_episode(world, net_bc, horizon=horizon, label_hook=hook,
                                   replay_check=False, far_share=False)
        cpu_world = time.process_time() - c0
        if len(labelled) != ep["student"]["forward_passes"]:
            raise AssertionError("one label per forward-pass decision")
        verified = None
        if verify:
            ref = S.run_student_episode(world, net_bc, horizon=horizon, replay_check=False,
                                        far_share=False)
            verified = (ref["coverage_backhauled"] == ep["coverage_backhauled"]
                        and np.array_equal(ref["targets"], ep["targets"]))
            if not verified:
                raise AssertionError(f"world {world}: relabelling changed the student roll-in")
        cpu_label += label_cpu[0]
        for lab in labelled:
            xs.append(np.asarray(lab["features"], dtype=np.float64))
            ys.append(lab["layouts"])
        row = {"world": world, "all_mean": ep["all_mean"], "final_100_mean": ep["final_100_mean"],
               "forward_passes": ep["student"]["forward_passes"], "labelled": len(labelled),
               "label_planner_cpu_s": label_cpu[0], "rollin_cpu_s_incl_labels": cpu_world,
               "rollin_unchanged_without_labels": verified}
        rows.append(row)
        if out_dir is not None:
            from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import write_json
            write_json(Path(out_dir) / f"{world}.json",
                       {"world": world, "horizon": int(horizon), "budget": int(budget),
                        "label_seeds": list(seeds), "all_mean": ep["all_mean"],
                        "final_100_mean": ep["final_100_mean"],
                        "coverage_backhauled": ep["coverage_backhauled"],
                        "decision_record": ep["decisions"], "labelled": labelled}, indent=None)
        if log is not None:
            log(f"dagger world={world} S_bc={ep['all_mean']:.4f} forward={row['forward_passes']} "
                f"label_cpu={label_cpu[0]:.2f}s world_cpu={cpu_world:.2f}s verified={verified}")
    X = np.stack(xs) if xs else np.zeros((0, S.IN_DIM))
    Y = np.stack(ys) if ys else np.zeros((0, len(seeds), N_UAVS, 3))
    readings = {"worlds": [int(w) for w in worlds], "per_world": rows, "n": int(X.shape[0]),
                "K": len(seeds), "seeds": list(seeds), "budget": int(budget),
                "label_planner_cpu_s": cpu_label,
                "rollin_all_mean": float(np.mean([r["all_mean"] for r in rows])) if rows else None,
                "label_rule": ("every student decision that ran a forward pass (known set changed / "
                               "first >= 6 known); cache-hit decisions carry the same known set and "
                               "are not relabelled")}
    return X, Y, readings


# ============================================================ full exposure


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def open_loop(nets: dict[str, S.StudentNet], X: np.ndarray, Y: np.ndarray) -> dict[str, Any]:
    """Per checkpoint: full-K loss and the seed-0-only (K = 1) loss."""
    out = {}
    for name, net in nets.items():
        out[name] = {"K_full": dataset_loss(net, X, Y), "K1_seed0": dataset_loss(net, X, Y, k_first=1)}
    return out


def train_all(segment_a_dir: Path, dagger_worlds: Sequence[int], out: Path,
              epochs_a: int = EPOCHS_A, epochs_b: int = EPOCHS_B, budget: int = PLANNER_BUDGET,
              horizon: int = S.HORIZON, log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """S0 -> S_bc (segment A) -> DAgger round -> S (A u B, fresh Adam); writes checkpoints."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    X_A, Y_A, meta_a = load_segment(segment_a_dir)
    if meta_a["seeds"] != list(LABEL_SEEDS):
        raise ValueError(f"segment A seeds {meta_a['seeds']} != declared {list(LABEL_SEEDS)}")
    phases: dict[str, Any] = {}
    ckpt: dict[str, Any] = {}

    net = S.make_net()
    base_meta = {"architecture": S.ARCHITECTURE, "init_seed": S.INIT_SEED}
    ckpt["s0"] = S.save_checkpoint(net, out / "s0.pt", {**base_meta, "name": "S0", "trained_epochs": 0})
    s0 = copy.deepcopy(net)

    phases["segment_A"] = fit(net, X_A, Y_A, epochs_a, log=log)
    ckpt["s_bc"] = S.save_checkpoint(net, out / "s_bc.pt",
                                     {**base_meta, "name": "S_bc", "trained_epochs": int(epochs_a),
                                      "segment_A": meta_a["files_digest_sha256"]})
    s_bc = copy.deepcopy(net)

    c0 = time.process_time()
    X_B, Y_B, dag = dagger_round(s_bc, dagger_worlds, budget=budget, horizon=horizon, log=log,
                                 out_dir=out / "dagger")
    dag["cpu_s"] = time.process_time() - c0
    phases["dagger"] = dag
    X_AB, Y_AB = np.concatenate([X_A, X_B]), np.concatenate([Y_A, Y_B])
    phases["segment_B"] = fit(net, X_AB, Y_AB, epochs_b, log=log)   # fresh Adam inside fit
    ckpt["s"] = S.save_checkpoint(net, out / "s.pt",
                                  {**base_meta, "name": "S", "trained_epochs": int(epochs_a + epochs_b),
                                   "segment_A": meta_a["files_digest_sha256"],
                                   "segment_B_n": int(X_B.shape[0])})
    for name in ckpt:
        ckpt[name] = {**ckpt[name], "pt_sha256": _sha256(ckpt[name]["pt"]),
                      "json_sha256": _sha256(ckpt[name]["json"])}
    nets = {"S0": s0, "S_bc": s_bc, "S": net}
    train_readings = {"segment_A": open_loop(nets, X_A, Y_A),
                      "segment_B": open_loop(nets, X_B, Y_B) if X_B.shape[0] else None}
    return {"nets": nets, "checkpoints": ckpt, "phases": phases,
            "data": {"segment_A": meta_a, "N_A": int(X_A.shape[0]), "N_B": int(X_B.shape[0]),
                     "K": int(Y_A.shape[1])},
            "train_open_loop": train_readings,
            "declared": {"epochs_a": EPOCHS_A, "epochs_b": EPOCHS_B, "lr": LR, "batch": BATCH,
                         "shuffle_seed": SHUFFLE_SEED, "init_seed": S.INIT_SEED,
                         "budget": PLANNER_BUDGET, "horizon": S.HORIZON,
                         "dagger_worlds": [DAGGER_WORLDS[0], DAGGER_WORLDS[-1]],
                         "label_seeds": list(LABEL_SEEDS)},
            "used": {"epochs_a": int(epochs_a), "epochs_b": int(epochs_b), "budget": int(budget),
                     "horizon": int(horizon), "dagger_worlds": [int(w) for w in dagger_worlds]}}
