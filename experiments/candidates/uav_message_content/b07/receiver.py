"""B07-only frozen receiver adapter; original B05 forward remains unchanged."""

import io

import torch

from experiments.candidates.uav_message_content.b05.model import Actor as ResidualActor, BaseActor
from .contract import B_SHA, D_SHA, require


class Receiver(ResidualActor):
    def components(self, observations, hidden):
        require(observations.shape[-1] == 186, "D receiver input size")
        base, recurrent, next_hidden = self.base(observations[..., :171], hidden)
        correction = .1 * torch.tanh(self.residual_output(torch.tanh(
            self.residual_hidden(torch.cat((observations, recurrent), -1)))))
        return base + correction, recurrent, next_hidden, base, correction


def parameter_hash(actor):
    import hashlib
    digest = hashlib.sha256()
    for name, tensor in actor.state_dict().items():
        digest.update(name.encode() + b"\0" + tensor.detach().numpy().tobytes())
    return digest.hexdigest()


def load_receiver(path, kind):
    from .contract import sha256
    require(kind in ("D", "B") and sha256(path) == (D_SHA if kind == "D" else B_SHA),
            "receiver checkpoint identity")
    state = torch.load(io.BytesIO(path.read_bytes()), map_location="cpu", weights_only=True)
    expected = dict(arm=kind, master=19702 if kind == "D" else 19451,
                    input_size=186 if kind == "D" else 171, critic_size=526 if kind == "D" else 451)
    require(all(state.get(k) == v for k, v in expected.items()), "receiver metadata")
    if kind == "D":
        require(state.get("inherited_sha256") == B_SHA and state.get("correction_bound") == .1,
                "D inheritance")
    # Constructors cannot affect the separately seeded motion or fit generators.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0)
        actor = Receiver() if kind == "D" else BaseActor()
    actor.load_state_dict(state["actor"], strict=True)
    actor.requires_grad_(False)
    actor.eval()
    require(all(bool(torch.isfinite(p).all()) for p in actor.parameters()), "nonfinite receiver")
    return actor


def forward_step(actor, x, hidden, kind):
    return actor(x[None, :, :171] if kind == "B" else x[None], hidden)
