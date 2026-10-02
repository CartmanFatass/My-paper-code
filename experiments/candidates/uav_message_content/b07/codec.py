"""FP32 direct metric search and literal hard-forward/soft-backward dictionary."""

import numpy as np
import torch

from .contract import CENTERS, increment, require


def validate_book(book, scales):
    require(book.shape == (CENTERS, 6) and scales.shape == (6,), "codec dimensions")
    require(book.dtype == scales.dtype == torch.float32 and book.device.type == scales.device.type == "cpu",
            "codec CPU FP32 required")
    require(bool(torch.isfinite(book).all() and torch.isfinite(scales).all()) and
            bool(((book >= 0) & (book <= 1)).all()) and bool((scales > 0).all()), "codec values")


def distances(source, book, scales, counts=None):
    require(source.shape[-1] == 6 and bool(torch.isfinite(source).all()), "source values")
    if counts is not None:
        increment(counts, "nearest_center_comparisons", source.numel() // 6 * len(book))
    return (((source[..., None, :] - book) * scales) ** 2).sum(-1)


class _HardForward(torch.autograd.Function):
    @staticmethod
    def forward(ctx, hard, soft):
        # A literal lookup clone: never arithmetic cancellation with soft values.
        return hard.clone()

    @staticmethod
    def backward(ctx, gradient):
        return None, gradient


def reconstruct(source, book, scales, temperature=None, counts=None):
    d = distances(source, book, scales, counts)
    indices = d.argmin(-1)  # torch argmin's first index is the exact tie rule.
    hard = book[indices]
    if temperature is None:
        return hard, indices
    require(temperature > 0, "positive temperature required")
    soft = torch.softmax(-d / temperature, -1) @ book
    return _HardForward.apply(hard, soft), indices


def metric_scales(samples, metric):
    if metric == "unit":
        return torch.ones(6)
    require(metric == "inverse_sd", "unknown metric")
    return samples.std(0, unbiased=False).clamp_min(.05).reciprocal()


@torch.no_grad()
def fit_ordinary(samples, scales, seed, counts, progress=lambda _, __: None):
    """Exactly 256 initialization visits, 25 Lloyd passes and final assignment."""
    require(samples.ndim == 2 and samples.shape[1] == 6 and len(samples) >= CENTERS,
            "insufficient source rows")
    require(samples.dtype == torch.float32 and bool(((samples >= 0) & (samples <= 1)).all()),
            "source range/dtype")
    rng = np.random.default_rng(seed)
    chosen = [int(rng.integers(len(samples)))]
    best = distances(samples, samples[chosen], scales, counts)[:, 0]
    for _ in range(1, CENTERS):
        mass = best.double().numpy()
        mass[np.asarray(chosen)] = 0
        total = float(mass.sum())
        index = int(rng.choice(len(samples), p=mass / total)) if total > 0 else next(
            i for i in range(len(samples)) if i not in chosen)
        chosen.append(index)
        best = torch.minimum(best, distances(samples, samples[index:index + 1], scales, counts)[:, 0])
    book = samples[chosen].clone()
    initial_book = book.clone()
    history = []
    for iteration in range(25):
        d = distances(samples, book, scales, counts)
        labels = d.argmin(1)
        error = d.gather(1, labels[:, None])[:, 0]
        # Stable source-row tie order; each empty cluster gets a distinct row.
        candidates = torch.argsort(error, descending=True, stable=True).tolist()
        used = set()
        updated = []
        for k in range(CENTERS):
            assigned = samples[labels == k]
            if len(assigned):
                updated.append(assigned.mean(0))
            else:
                index = next(i for i in candidates if i not in used)
                used.add(index)
                updated.append(samples[index])
        book = torch.stack(updated).clamp(0, 1)
        row = dict(iteration=iteration, mean_squared_metric_error=float(error.mean()),
                   empty_clusters=len(used))
        history.append(row)
        progress(row, book)
    d = distances(samples, book, scales, counts)
    return book, initial_book, history, float(d.min(1).values.mean())
