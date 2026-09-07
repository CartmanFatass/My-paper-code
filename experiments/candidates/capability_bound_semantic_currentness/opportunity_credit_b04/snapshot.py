"""Explicit B04 learner snapshots; no resume or old GAE metadata."""
from dataclasses import asdict
import torch
from .learner import OBJECT


def same_state(left, right):
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype and left.shape == right.shape
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            same_state(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right):
            same_state(a, b)
    else:
        assert left == right


def snapshot_readback(path, trainer, **metadata):
    payload = {"object": OBJECT, "seed": trainer.seed, "rng_namespace": trainer.run_name,
               "configuration": asdict(trainer.config), "metadata": metadata,
               "model": trainer.model.state_dict(), "optimizer": trainer.optimizer.state_dict(),
               "counters": asdict(trainer.counters),
               "minibatch_order_digest": trainer.minibatch_order_digest,
               "initialization_digest": trainer.model.initialization_digest}
    torch.save(payload, path)
    reread = torch.load(path, map_location="cpu", weights_only=True)
    same_state(payload, reread)
    return reread
