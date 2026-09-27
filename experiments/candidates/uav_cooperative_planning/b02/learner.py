"""One fixed CPU fitted action-value procedure for B02."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
import torch

from .controller import MAX_CANDIDATES, WIDTH

FIT_SEED = 29092791
UPDATES = 5000
BATCH = 256
DISCOUNT = 0.97


class CandidateValue(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(WIDTH, 128), torch.nn.ReLU(),
            torch.nn.Linear(128, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
        )
        torch.nn.init.zeros_(self.net[-1].weight)
        torch.nn.init.zeros_(self.net[-1].bias)

    def forward(self, features):
        return self.net(features).squeeze(-1)


def parameter_digest(model):
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        array = value.detach().cpu().contiguous().numpy()
        digest.update(array.tobytes())
    return digest.hexdigest()


class FrozenValue:
    def __init__(self, checkpoint: Path):
        record = torch.load(checkpoint, map_location="cpu", weights_only=True)
        self.mean = np.asarray(record["mean"], dtype=np.float32)
        self.scale = np.asarray(record["scale"], dtype=np.float32)
        if (self.mean.shape != (WIDTH,) or self.scale.shape != (WIDTH,)
                or not np.isfinite(self.mean).all() or not np.isfinite(self.scale).all()
                or np.any(self.scale <= 0)):
            raise ValueError("invalid fixed collection normalization")
        with torch.random.fork_rng(devices=[]):
            self.net = CandidateValue()
        self.net.load_state_dict(record["model"])
        self.net.eval()

    def __call__(self, features, mask):
        n = int(np.count_nonzero(mask))
        if n < 1 or np.any(mask != (np.arange(MAX_CANDIDATES) < n)):
            raise ValueError("candidate mask is not contiguous")
        values = (features[:n] - self.mean) / self.scale
        if not np.isfinite(values).all():
            raise FloatingPointError("nonfinite normalized evaluation input")
        with torch.no_grad():
            answer = self.net(torch.from_numpy(values)).numpy()
        return answer


def fit(collection_paths: list[Path], checkpoint: Path, progress):
    """Load the sole collection, normalize valid candidates, and run one fixed fit."""
    if checkpoint.exists():
        raise FileExistsError(checkpoint)
    worlds = []
    for path in collection_paths:
        with np.load(path, allow_pickle=False) as archive:
            worlds.append({name: archive[name].copy() for name in
                           ("features", "mask", "chosen_index", "macro_reward",
                            "terminal", "next_index")})
    for world in worlds:
        n = len(world["chosen_index"])
        if (n < 1 or not np.array_equal(world["next_index"],
                                        np.r_[np.arange(1, n, dtype=np.int32), -1])
                or not np.array_equal(world["terminal"],
                                      np.r_[np.zeros(n - 1, dtype=bool), True])):
            raise ValueError("collection successor chain or terminal boundary changed")
    features = np.concatenate([world["features"] for world in worlds])
    mask = np.concatenate([world["mask"] for world in worlds])
    chosen = np.concatenate([world["chosen_index"] for world in worlds]).astype(np.int64)
    rewards = np.concatenate([world["macro_reward"] for world in worlds]).astype(np.float32)
    terminal = np.concatenate([world["terminal"] for world in worlds]).astype(bool)
    offsets = np.cumsum([0] + [len(world["chosen_index"]) for world in worlds[:-1]])
    next_index = np.concatenate([world["next_index"] + offset
                                 for world, offset in zip(worlds, offsets)]).astype(np.int64)
    count = len(chosen)
    if (features.shape != (count, MAX_CANDIDATES, WIDTH) or mask.shape != (count, MAX_CANDIDATES)
            or count == 0 or not np.isfinite(features[mask]).all()
            or not np.isfinite(rewards).all()
            or np.any(chosen < 0) or np.any(chosen >= MAX_CANDIDATES)
            or np.any(~mask[np.arange(count), chosen])
            or np.any(next_index[~terminal] >= count)
            or np.any(next_index[~terminal] < 0)):
        raise ValueError("collection tuple geometry, values or successor indices invalid")
    valid = features[mask].astype(np.float64)
    mean = valid.mean(axis=0).astype(np.float32)
    scale = valid.std(axis=0).astype(np.float32)
    scale[scale == 0] = 1.0
    if not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise FloatingPointError("nonfinite collection normalization")
    normalized = np.zeros_like(features, dtype=np.float32)
    normalized[mask] = ((features[mask] - mean) / scale).astype(np.float32)
    if not np.isfinite(normalized[mask]).all():
        raise FloatingPointError("nonfinite normalized collection")
    torch.manual_seed(FIT_SEED)
    torch.set_num_threads(1)
    model = CandidateValue()
    target = copy.deepcopy(model)
    initial = parameter_digest(model)
    initial_state = [parameter.detach().clone() for parameter in model.parameters()]
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=0)
    x = torch.from_numpy(normalized)
    m = torch.from_numpy(mask)
    r = torch.from_numpy(rewards)
    sampled = np.random.default_rng(FIT_SEED)
    last_loss = None
    target_forward_rows = 0
    target_valid_candidates = 0
    for update in range(1, UPDATES + 1):
        ids = torch.from_numpy(sampled.integers(0, count, size=BATCH, dtype=np.int64))
        selected = x[ids, torch.from_numpy(chosen[ids.numpy()])]
        prediction = model(selected)
        label = r[ids] / 10.0
        live = ~terminal[ids.numpy()]
        if np.any(live):
            live_indices = np.flatnonzero(live)
            successors = torch.from_numpy(next_index[ids.numpy()[live]])
            target_forward_rows += int(len(successors) * MAX_CANDIDATES)
            target_valid_candidates += int(m[successors].sum())
            with torch.no_grad():
                values = target(x[successors])
                values = values.masked_fill(~m[successors], -torch.inf)
                best = values.max(dim=1).values
                if not torch.isfinite(best).all():
                    raise FloatingPointError("nonfinite target continuation")
                label[live_indices] += DISCOUNT * best
        loss = torch.mean((prediction - label) ** 2)
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite Bellman regression")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        if any(not torch.isfinite(parameter).all() for parameter in model.parameters()):
            raise FloatingPointError("nonfinite fitted parameter")
        if update % 100 == 0:
            target.load_state_dict(model.state_dict())
            progress({"updates": update, "target_copies": update // 100,
                      "last_loss": float(loss), "last_gradient_norm": float(norm),
                      "target_forward_rows": target_forward_rows,
                      "target_valid_candidates": target_valid_candidates})
        last_loss = float(loss)
    movement = float(torch.sqrt(sum(torch.sum((parameter - start) ** 2)
                                    for parameter, start in zip(model.parameters(), initial_state))))
    final = parameter_digest(model)
    if not np.isfinite(movement) or not np.isfinite(last_loss):
        raise FloatingPointError("nonfinite fit reading")
    payload = {"model": model.state_dict(), "mean": torch.from_numpy(mean),
               "scale": torch.from_numpy(scale),
               "configuration": {"architecture": [248, 128, 64, 1],
                                 "activation": "ReLU", "final_layer_initialization": "zero",
                                 "optimizer": "Adam", "learning_rate": 0.001,
                                 "batch_size": BATCH, "updates": UPDATES,
                                 "discount_per_macro": DISCOUNT,
                                 "target_copy_interval": 100, "gradient_norm_cap": 1,
                                 "fit_seed": FIT_SEED,
                                 "sampling_seed": FIT_SEED,
                                 "normalization": "valid candidate population mean/std; constant scale one"},
               "updates": UPDATES, "initial_sha256": initial,
               "final_sha256": final, "parameter_l2_movement": movement}
    temporary = checkpoint.with_suffix(".tmp")
    torch.save(payload, temporary)
    temporary.replace(checkpoint)
    return {"fit_seed": FIT_SEED, "updates": UPDATES, "sampled_transitions": UPDATES * BATCH,
            "target_copies": UPDATES // 100, "initial_sha256": initial,
            "final_sha256": final, "parameter_l2_movement": movement,
            "last_loss": last_loss, "collection_transitions": count,
            "target_forward_rows": target_forward_rows,
            "target_valid_candidates": target_valid_candidates,
            "multi_option_transitions": int(np.count_nonzero(mask.sum(axis=1) > 1)),
            "forced_transitions": int(np.count_nonzero(mask.sum(axis=1) == 1)),
            "collection_candidate_rows": int(mask.sum())}
