"""Strict, frozen loading of the four selected actor endpoints."""

import hashlib
import io
from pathlib import Path

import torch
from torch import nn

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm as build_cadc_arm

INHERITED_SHA256 = "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"
ASSETS = {
    "C": dict(master=19431, bytes=463293, sha256=INHERITED_SHA256),
    "B": dict(master=19451, bytes=463357,
              sha256="34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"),
    "O": dict(master=19452, bytes=463357,
              sha256="90760a722081dec5442aeec85c9302ae3992dcfb96f0bf919aa81389815aa684"),
    "L": dict(master=19452, bytes=464366,
              sha256="c8df7428611608ae0c2786b6b9e395e8183d3b79b30fcdd197e4fcdc9c643f59"),
}


def actor_state_sha256(actor):
    digest = hashlib.sha256()
    for name, tensor in sorted(actor.state_dict().items()):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("ascii") + b"\0")
        digest.update(str(tuple(value.shape)).encode("ascii") + b"\0")
        digest.update(str(value.dtype).encode("ascii") + b"\0")
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def load_asset(label, root, *, specification=ASSETS):
    if label not in specification:
        raise ValueError(f"unknown frozen asset {label}")
    declared = specification[label]
    path = Path(root) / f"{label}.pt"
    checkpoint_bytes = path.read_bytes()
    actual_sha = hashlib.sha256(checkpoint_bytes).hexdigest()
    if len(checkpoint_bytes) != declared["bytes"] or actual_sha != declared["sha256"]:
        raise ValueError(f"{label} checkpoint bytes/digest mismatch")
    # Parse exactly the bytes just verified, never a second read of the path.
    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    expected_keys = {"actor", "critic", "arm", "master", "input_size", "critic_size"}
    if label != "C":
        expected_keys.add("inherited_sha256")
    if not isinstance(state, dict) or set(state) != expected_keys:
        raise ValueError(f"{label} checkpoint metadata keys mismatch")
    if (state["arm"], state["master"], state["input_size"], state["critic_size"]) != (
            label, declared["master"], 171, 451):
        raise ValueError(f"{label} checkpoint metadata mismatch")
    if label != "C" and state["inherited_sha256"] != INHERITED_SHA256:
        raise ValueError(f"{label} inherited checkpoint mismatch")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * declared["master"] + 11)
        actor, critic = build_cadc_arm(19431, "RR")
        if label == "L":
            torch.manual_seed(100000 * declared["master"] + 12)
            actor.content = nn.Linear(64, 1)
            actor.content_log_std = nn.Parameter(torch.zeros(1))
    for name, saved, expected in (("actor", state["actor"], actor.state_dict()),
                                  ("critic", state["critic"], critic.state_dict())):
        if not isinstance(saved, dict) or set(saved) != set(expected):
            raise ValueError(f"{label} {name} tensor keys mismatch")
        if any(not isinstance(value, torch.Tensor) or value.dtype != torch.float32 or
               value.shape != expected[key].shape or not torch.isfinite(value).all()
               for key, value in saved.items()):
            raise ValueError(f"{label} {name} tensor contract mismatch")
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.eval()
    actor.requires_grad_(False)
    return actor, dict(path=str(path), sha256=actual_sha, bytes=len(checkpoint_bytes),
                       arm=label, master=declared["master"],
                       inherited_sha256=state.get("inherited_sha256"))


def sample_content(actor, recurrent, sender, rng):
    if not hasattr(actor, "content"):
        raise ValueError("only L samples content")
    mean = actor.content(recurrent[sender])
    pre_tanh = mean + actor.content_log_std.clamp(-5, 2).exp() * torch.randn(
        1, generator=rng)
    return pre_tanh, (1 + pre_tanh.tanh()) / 2
