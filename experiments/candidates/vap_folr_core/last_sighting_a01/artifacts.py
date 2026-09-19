"""Recoverable final trajectories and content digests for A01."""

import hashlib
from pathlib import Path

import numpy as np


def array_digest(arrays):
    """Hash semantic array content independently of NPZ container metadata."""
    digest = hashlib.sha256()
    for name in sorted(arrays):
        value = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(value.dtype.str.encode("ascii") + b"\0")
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def write_panel(path, episodes):
    """Retain every collected final observation, action, reward and terminal."""
    if not episodes:
        raise ValueError("cannot publish an empty final panel")
    keys = tuple(episodes[0])
    if any(tuple(episode) != keys for episode in episodes):
        raise ValueError("final episodes have inconsistent array keys")
    arrays = {key: np.stack([episode[key] for episode in episodes]) for key in keys}
    if arrays["reward"].ndim != 2 or arrays["reward"].shape[1] != 20:
        raise ValueError("final panel requires complete H20 trajectories")
    path = Path(path)
    np.savez_compressed(path, **arrays)
    return {
        "path": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "content_sha256": array_digest(arrays),
        "arrays": sorted(arrays),
        "episodes": len(episodes),
        "transitions": int(arrays["reward"].size),
    }

