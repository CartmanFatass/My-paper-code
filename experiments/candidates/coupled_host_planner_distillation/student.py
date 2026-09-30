"""Student S (coupled_host_planner_distillation, cell b01 piece 3): layout-level policy, no search.

Authority: ``docs/research/candidates/coupled_host_planner_distillation/NOTES.md``, entry "REVISED
PRE-DECLARATION" (commit d62bb0bb1) items 2 and 4-5, the 03:14 fact entry (18-output head), the
piece-2 acceptance (targets = layout[assign_targets(current positions, layout)] at every decision)
and the piece-3 L0 scope note with its two amendments (K = 1 open-loop metric; JSON checkpoints).

* ``StudentNet``: MLP 168 -> 256 -> 256 -> 18, ReLU, **float32**; output o (6 sites x 3) mapped
  to the box by ``x, y = 2500 (1 + tanh o)``, ``z = 100 + 50 tanh o`` (z in [50, 150]).  In the
  box-normalised coordinates of the loss (x / 5000, y / 5000, (z - 50) / 100) every component is
  ``(1 + tanh o) / 2``.  Init: ``torch.manual_seed(932201)`` immediately before construction (S0).
  float32 is fixed so that the JSON checkpoint (float32 values) reproduces the .pt bit for bit.
* ``layout_loss``: for every item, min over the K teacher layouts and the 720 site permutations
  of the mean over sites of the squared box-normalised distance; batch mean.  Computed from the
  6 x 6 pairwise cost matrix gathered by the precomputed 720 x 6 permutation index (identical to
  the B x K x 720 x 6 x 3 expansion, cheaper).
* ``StudentArm``: T_M's machinery (``TeacherMarkov``: pooling every host step, decisions at
  t % 10 == 0, hold at spawn while < 6 known, re-decide iff the known set changed, re-assignment
  at the current positions at every decision) with the planner call replaced by ONE forward pass
  on ``features_shared(map, positions)``.  The arm never references a planner function;
  ``record`` asserts zero planner evaluations.  An optional ``label_hook`` (DAgger relabelling)
  is called from ``targets`` AFTER the decision's targets are fixed and returned by the hold; it
  receives copies and cannot change them.
* ``run_student_episode``: closed loop on ``B4.make_static_host`` (reset(seed = world)), replay
  check, CPU split (forward / assign / rest) and the harness-side far-cluster backhauled share.
"""

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import torch
from torch import nn

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import MACRO_K, N_UAVS, N_USERS
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    backhauled_users_mask,
    cluster_layout,
)
from experiments.candidates.coupled_host_planner_distillation import teacher as T
from experiments.candidates.coupled_host_planner_distillation import teacher_markov as TM
from experiments.candidates.coupled_host_replan_timing.rules import rollout

torch.set_num_threads(1)

INIT_SEED = 932201
IN_DIM = TM.SHARED_FEATURE_DIM            # 168
HIDDEN = (256, 256)
OUT_DIM = N_UAVS * 3                      # 18: 6 sites x (x, y, z)
DTYPE = torch.float32
HORIZON = T.HORIZON
PERMUTATIONS = torch.tensor(list(itertools.permutations(range(N_UAVS))), dtype=torch.long)  # 720 x 6
ARCHITECTURE = {"in": IN_DIM, "hidden": list(HIDDEN), "out": OUT_DIM, "activation": "relu",
                "output_map": "x, y = 2500 (1 + tanh); z = 100 + 50 tanh", "dtype": "float32",
                "init": f"torch.manual_seed({INIT_SEED}) then default nn.Linear init"}
USER_PERM_SEED_TAG = 7                   # permuted-index reading: default_rng([world, 7])


# ============================================================ network and loss


class StudentNet(nn.Module):
    """168 -> 256 -> 256 -> 18; ``forward`` returns box-normalised sites [B, 6, 3] in [0, 1]."""

    def __init__(self) -> None:
        super().__init__()
        self.body = nn.Sequential(nn.Linear(IN_DIM, HIDDEN[0]), nn.ReLU(),
                                  nn.Linear(HIDDEN[0], HIDDEN[1]), nn.ReLU(),
                                  nn.Linear(HIDDEN[1], OUT_DIM))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return 0.5 * (1.0 + torch.tanh(self.body(x))).reshape(-1, N_UAVS, 3)


def make_net(seed: int = INIT_SEED) -> StudentNet:
    torch.manual_seed(int(seed))
    return StudentNet().to(DTYPE)


def normalise(xyz: np.ndarray | torch.Tensor):
    """Metres -> box-normalised (x / 5000, y / 5000, (z - 50) / 100)."""
    scale = np.array([T.AREA_M, T.AREA_M, T.Z_SPAN_M])
    shift = np.array([0.0, 0.0, T.Z_LOW_M])
    if isinstance(xyz, torch.Tensor):
        return (xyz - torch.as_tensor(shift, dtype=xyz.dtype)) / torch.as_tensor(scale, dtype=xyz.dtype)
    return (np.asarray(xyz, dtype=np.float64) - shift) / scale


def to_metres(unit_xyz: np.ndarray) -> np.ndarray:
    """Box-normalised -> metres: x, y = 5000 u = 2500 (1 + tanh); z = 50 + 100 u = 100 + 50 tanh."""
    u = np.asarray(unit_xyz, dtype=np.float64)
    return np.stack([u[..., 0] * T.AREA_M, u[..., 1] * T.AREA_M, T.Z_LOW_M + u[..., 2] * T.Z_SPAN_M], -1)


def per_item_loss(pred: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """[B] min over K and the 720 permutations of the mean site squared distance (normalised)."""
    if pred.ndim != 3 or pred.shape[1:] != (N_UAVS, 3):
        raise ValueError(f"pred must be [B, 6, 3], got {tuple(pred.shape)}")
    if targets.ndim != 4 or targets.shape[0] != pred.shape[0] or targets.shape[2:] != (N_UAVS, 3):
        raise ValueError(f"targets must be [B, K, 6, 3], got {tuple(targets.shape)}")
    # cost[b, k, i, j] = || pred_b,i - y_b,k,j ||^2
    cost = ((pred[:, None, :, None, :] - targets[:, :, None, :, :]) ** 2).sum(-1)
    rows = torch.arange(N_UAVS)
    per_perm = cost[:, :, rows[None, :], PERMUTATIONS].mean(-1)      # [B, K, 720]
    return per_perm.reshape(pred.shape[0], -1).min(dim=1).values


def layout_loss(pred: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Scalar: batch mean of ``per_item_loss`` (both arguments box-normalised)."""
    return per_item_loss(pred, targets).mean()


# ============================================================ checkpoints (.pt and .json)


def save_checkpoint(net: StudentNet, path_pt: Path, meta: dict[str, Any]) -> dict[str, Any]:
    """Write ``<name>.pt`` (state_dict + meta) and ``<name>.json`` (float32 nested lists + meta)."""
    path_pt = Path(path_pt)
    path_pt.parent.mkdir(parents=True, exist_ok=True)
    state = {k: v.detach().clone() for k, v in net.state_dict().items()}
    torch.save({"state_dict": state, "meta": meta}, path_pt)
    parts = []
    for k, v in state.items():
        parts.append(f"{json.dumps(k)}:{{\"shape\":{json.dumps(list(v.shape))},"
                     f"\"values\":[{_float32_text(v.numpy())}]}}")
    text = (f"{{\"meta\":{json.dumps(meta, separators=(',', ':'), allow_nan=False)},"
            f"\"dtype\":\"float32\",\"state_dict\":{{{','.join(parts)}}}}}\n")
    path_json = path_pt.with_suffix(".json")
    tmp = path_json.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path_json)
    load_checkpoint(path_json)                       # both files present: asserts exact agreement
    return {"pt": str(path_pt), "json": str(path_json)}


def _float32_text(array: np.ndarray) -> str:
    """Comma-joined decimals that parse (JSON double -> float32) back to the exact float32 values.

    Shortest float32 repr per value; a value whose shortest repr would not survive the
    double -> float32 conversion is written as its exact double repr instead.
    """
    values = np.asarray(array, dtype=np.float32).reshape(-1)
    if not np.all(np.isfinite(values)):
        raise ValueError("non-finite parameter")
    texts = [str(x) for x in values]
    back = np.array([float(t) for t in texts], dtype=np.float64).astype(np.float32)
    for i in np.flatnonzero(back.view(np.uint32) != values.view(np.uint32)):
        texts[i] = repr(float(values[i]))
    return ",".join(texts)


def _net_from_state(state: dict[str, torch.Tensor]) -> StudentNet:
    net = StudentNet().to(DTYPE)
    net.load_state_dict(state)
    net.eval()
    return net


def load_checkpoint(path: Path) -> tuple[StudentNet, dict[str, Any]]:
    """Load from ``<name>.json`` and/or ``<name>.pt``; JSON preferred; both present -> must agree.

    Agreement: identical parameters and a bit-identical forward pass on a fixed input.
    """
    path = Path(path)
    base = path.with_suffix("")
    pj, pp = base.with_suffix(".json"), base.with_suffix(".pt")
    net_j = net_p = None
    meta: dict[str, Any] = {}
    if pj.exists():
        payload = json.loads(pj.read_text(encoding="utf-8"))
        state = {k: torch.tensor(np.asarray(v["values"], dtype=np.float32).reshape(v["shape"]))
                 for k, v in payload["state_dict"].items()}
        net_j, meta = _net_from_state(state), payload["meta"]
    if pp.exists():
        blob = torch.load(pp, map_location="cpu", weights_only=True)
        net_p = _net_from_state(blob["state_dict"])
        meta = meta or blob["meta"]
    if net_j is None and net_p is None:
        raise FileNotFoundError(f"no checkpoint at {pj} or {pp}")
    if net_j is not None and net_p is not None:
        for (k, a), (_k, b) in zip(net_j.state_dict().items(), net_p.state_dict().items()):
            if not torch.equal(a, b):
                raise AssertionError(f"{base}: .json and .pt disagree on {k}")
        probe = torch.from_numpy(np.random.default_rng(0).uniform(0, 1, (4, IN_DIM))).to(DTYPE)
        with torch.no_grad():
            if not torch.equal(net_j(probe), net_p(probe)):
                raise AssertionError(f"{base}: .json and .pt forward passes differ")
    return (net_j if net_j is not None else net_p), meta


# ============================================================ runtime arm


def permute_user_blocks(feat: np.ndarray, user_perm: np.ndarray) -> np.ndarray:
    """User ``u``'s [known, x, y] block moves to slot ``user_perm[u]``; UAV blocks unchanged."""
    out = np.array(feat, copy=True)
    users = np.asarray(feat[: N_USERS * 3]).reshape(N_USERS, 3)
    permuted = np.empty_like(users)
    permuted[np.asarray(user_perm, dtype=int)] = users
    out[: N_USERS * 3] = permuted.reshape(-1)
    return out


def world_user_perm(world: int) -> np.ndarray:
    return np.random.default_rng([int(world), USER_PERM_SEED_TAG]).permutation(N_USERS)


class StudentArm(TM.TeacherMarkov):
    """T_M with the planner call replaced by one forward pass of ``net`` (no search anywhere)."""

    def __init__(self, env, world: int, net: StudentNet, user_perm: np.ndarray | None = None,
                 label_hook: Callable[..., None] | None = None, record: bool = True,
                 macro_k: int = MACRO_K) -> None:
        super().__init__(env, world, budget=0, seed=0, record=record, macro_k=macro_k)
        self.net = net
        self.net.eval()
        self.user_perm = None if user_perm is None else np.asarray(user_perm, dtype=int)
        if self.user_perm is not None and sorted(self.user_perm.tolist()) != list(range(N_USERS)):
            raise ValueError("user_perm must be a permutation of the 50 user ids")
        self.label_hook = label_hook
        self.forward_passes = 0
        self.cpu = {"forward_s": 0.0, "assign_s": 0.0, "planner_s": 0.0, "label_planner_s": 0.0}
        self.forward_cpu: list[float] = []
        self._pending: dict[str, Any] | None = None

    def targets(self, t: int) -> np.ndarray:
        out = super().targets(t)          # observe, then decide at boundaries (targets now fixed)
        pending, self._pending = self._pending, None
        if pending is not None and self.label_hook is not None:
            self.label_hook(self.env, np.array(pending["xy"], copy=True),
                            np.array(pending["positions"], copy=True), dict(pending))
        return out

    def _plan(self, t: int, known: frozenset, positions: np.ndarray) -> int:
        """ONE forward pass on the shared features; no planner call."""
        users, xy = self.map.users_xy()
        if frozenset(users) != known:
            raise AssertionError("known set and map users disagree")
        if known in self.cache:
            raise AssertionError("a previously decided known set recurred")
        c0 = time.process_time()
        feat = TM.features_shared(self.map, positions)
        net_in = feat if self.user_perm is None else permute_user_blocks(feat, self.user_perm)
        with torch.no_grad():
            unit = self.net(torch.from_numpy(net_in).to(DTYPE)[None])[0].double().numpy()
        layout = to_metres(unit)
        dt = time.process_time() - c0
        self.cpu["forward_s"] += dt
        self.forward_cpu.append(dt)
        self.forward_passes += 1
        self.layout, self.plan_set = layout, known
        self.cache[known] = layout
        self.plans.append({"decision_step": t, "n_known": len(users), "evaluations": 0,
                           "forward_cpu_s": dt})
        self._pending = {"step": t, "known": sorted(int(u) for u in users), "features": feat,
                         "positions": positions.copy(), "xy": xy.copy(), "layout": layout.copy()}
        if self.record_labels:
            self.labelled.append({"step": t, "known": self._pending["known"], "features": feat,
                                  "positions": positions.copy(), "layout": layout.copy()})
        return 0

    def record(self) -> dict[str, Any]:
        if self.evaluations != 0 or any(p["evaluations"] for p in self.plans):
            raise AssertionError("the student arm made a planner evaluation")
        return {
            "forward_passes": int(self.forward_passes),
            "forward_steps": [p["decision_step"] for p in self.plans],
            "cache_hits": int(sum(d["cache_hit"] for d in self.decisions)),
            "assignment_changes": int(sum(bool(d["assignment_changed"]) for d in self.decisions)),
            "hold_decisions": int(sum(d["hold"] for d in self.decisions)),
            "hold_steps": int(self.hold_steps), "users_known_terminal": len(self.map.latest),
            "decisions": len(self.decisions), "observe_calls": int(self.observe_calls),
            "planner_evaluations": 0, "user_permuted": self.user_perm is not None,
        }


def run_student(env, world: int, net: StudentNet, horizon: int = HORIZON,
                user_perm: np.ndarray | None = None, label_hook: Callable | None = None,
                step_hook: Callable[[int], None] | None = None) -> tuple[dict[str, Any], StudentArm]:
    """Student closed loop on a freshly reset host (not reset here); returns (rollout, arm).

    ``step_hook(t)`` (harness readings) is called before the arm's ``targets(t)``.
    """
    arm = StudentArm(env, world, net, user_perm=user_perm, label_hook=label_hook)
    if step_hook is None:
        targets_fn = arm.targets
    else:
        def targets_fn(t: int) -> np.ndarray:
            step_hook(int(t))
            return arm.targets(t)
    result = rollout(env, targets_fn, 0, int(horizon))
    arm.finish(result["t_end"])
    return result, arm


def run_student_episode(world: int, net: StudentNet, horizon: int = HORIZON,
                        user_perm: np.ndarray | None = None, label_hook: Callable | None = None,
                        replay_check: bool = True, far_share: bool = True) -> dict[str, Any]:
    """The student on a fresh static host (``B4.make_static_host``, ``reset(seed=world)``).

    Returns all-500 / final-100 C_bh, per-decision records (step, n_known, replanned = forward
    pass, targets), the forward-pass count and CPU, the CPU split (forward / assign / rest), the
    target replay check (a second fresh host, bit-identical C_bh and reward series) and, when
    ``far_share``, the far-cluster backhauled share of the state after every host step (harness
    reading: ``planner.cluster_layout`` membership from the reset state; the arm never sees it).
    """
    world = int(world)
    env = B4.make_static_host(world)
    env.reset(seed=world)
    T.check_host_constants(env)
    users0 = np.array(env.user_positions, dtype=float, copy=True)
    far_series: list[float] = []
    step_hook = None
    if far_share:
        layout = cluster_layout(env)
        members = np.asarray(layout["membership"]) == int(layout["far_cluster"])

        def step_hook(t: int) -> None:           # state after call t - 1
            if t > 0:
                h0 = time.process_time()
                far_series.append(float(np.mean(backhauled_users_mask(env)[members])))
                harness_cpu[0] += time.process_time() - h0
    harness_cpu = [0.0]
    c0 = time.process_time()
    result, arm = run_student(env, world, net, horizon, user_perm, label_hook, step_hook)
    cpu_total = time.process_time() - c0 - harness_cpu[0]       # the far-share reading excluded
    if far_share:
        far_series.append(float(np.mean(backhauled_users_mask(env)[members])))   # terminal state
    B4.assert_static(env, users0, "student")
    if result["t_end"] != int(horizon):
        raise AssertionError("student rollout ended early")
    targets = np.stack([d["targets"] for d in arm.decisions])
    if targets.shape != (int(horizon) // MACRO_K, N_UAVS, 3):
        raise AssertionError(f"targets shape {targets.shape}")
    if not np.all(np.isfinite(targets)):
        raise AssertionError("non-finite student targets")
    replay = None
    if replay_check:
        env_r = B4.make_static_host(world)
        env_r.reset(seed=world)
        rep = T.replay_labels(env_r, targets, horizon)
        replay = {"series_identical": rep["coverage_backhauled"] == result["coverage_backhauled"],
                  "contract_reward_identical": rep["contract_reward"] == result["contract_reward"]}
        if not (replay["series_identical"] and replay["contract_reward_identical"]):
            raise AssertionError(f"world {world}: target replay differs from the student closed loop")
    means = B4.series_means(result["coverage_backhauled"])
    rec = arm.record()
    cpu = arm.cpu
    decisions = [{"step": d["step"], "n_known": d["n_known"], "hold": d["hold"],
                  "replanned": d["replanned"], "cache_hit": d["cache_hit"],
                  "assignment_changed": d["assignment_changed"], "targets": d["targets"]}
                 for d in arm.decisions]
    far = None
    if far_share:
        far = {"mean_all": float(np.mean(far_series)), "final": far_series[-1],
               "steps": len(far_series)}
    return {
        "world": world, "horizon": int(horizon),
        "all_mean": means["all_mean"], "final_100_mean": means["final_100_mean"],
        "coverage_backhauled": result["coverage_backhauled"],
        "decisions": decisions, "targets": targets, "labelled": arm.labelled, "student": rec,
        "far_cluster_backhauled_share": far, "replay": replay,
        "forward_cpu_s": list(arm.forward_cpu),
        "cpu_s": {"forward": cpu["forward_s"], "assign": cpu["assign_s"],
                  "rest": cpu_total - cpu["forward_s"] - cpu["assign_s"], "total": cpu_total,
                  "harness_far_share_excluded": harness_cpu[0]},
    }
