"""EOCIV Stage 0 trainable models: common actor/backbone, critic, valve.

Licensed scope (Pro's acceptance ruling): instantiate and run FORWARD ONLY.
No parameter update of any kind happens in this module or in Stage 0 — the
optimizers built here are configured to the registered constants and never
stepped until Stage 1 is authorized.

The actor exposes exactly the ``CommonPolicy`` runner interface
(``initial_state()`` / ``forward(observations, active_mask, slot_block,
hidden, noise)``), so the Stage-0 outcome harness drives it through the SAME
accepted ``ArmEpisodeRunner`` binding path — receipt verification against the
actual slot tensor, ActionReceipt, bound_step — rather than a re-implemented
one (the ruling's "one authoritative implementation" requirement).

Architecture constants are registered in ``stage0_registration`` and asserted
here at construction; a drift between the registration and the built modules
is a Stage 0 abort, not a warning.
"""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import stage0_registration as reg

RAW_OUTPUT_BINDING = "eociv_lite.trainable_policy.v1"

SLOT_DIM = 32
SLOT_ENC_DIM = 16
ACTOR_HIDDEN = 32
CRITIC_IN = 11
VALVE_IN = 9
LOG_STD_INIT = math.log(0.2)

_torch_configured = False


def configure_torch() -> dict[str, object]:
    """Apply the registered determinism policy (idempotent) and report it."""
    global _torch_configured
    torch.set_num_threads(reg.TORCH_INTRA_OP_THREADS)
    if not _torch_configured:
        try:
            torch.set_num_interop_threads(reg.TORCH_INTER_OP_THREADS)
        except RuntimeError:
            # Interop pool already started; the manifest records the actual
            # value and the preflight compares it against the registration.
            pass
        _torch_configured = True
    torch.use_deterministic_algorithms(reg.TORCH_DETERMINISTIC_ALGORITHMS)
    return {
        "intra_op_threads": torch.get_num_threads(),
        "inter_op_threads": torch.get_num_interop_threads(),
        "deterministic_algorithms": reg.TORCH_DETERMINISTIC_ALGORITHMS,
        "dtype_policy": reg.DTYPE_POLICY,
        "device_policy": reg.DEVICE_POLICY,
    }


class EocivActor(nn.Module):
    """The one payload-aware common actor/backbone (registered contract 6.2)."""

    def __init__(self, actor_training_seed: int):
        super().__init__()
        assert reg.ACTOR_CONTRACT["recurrent"]["hidden"] == ACTOR_HIDDEN
        assert reg.ACTOR_CONTRACT["slot_encoder"]["out"] == SLOT_ENC_DIM
        self.actor_training_seed = int(actor_training_seed)
        torch.manual_seed(self.actor_training_seed)
        self.slot_encoder = nn.Linear(SLOT_DIM, SLOT_ENC_DIM)
        self.input_projector = nn.Linear(
            roster_env.OBSERVATION_DIM + SLOT_ENC_DIM, ACTOR_HIDDEN
        )
        self.cell = nn.GRUCell(ACTOR_HIDDEN, ACTOR_HIDDEN)
        self.action_head = nn.Linear(ACTOR_HIDDEN, roster_env.ACTION_DIM)
        self.log_std = nn.Parameter(
            torch.full((roster_env.ACTION_DIM,), LOG_STD_INIT)
        )

    def forward_step(
        self,
        observations: torch.Tensor,   # (capacity, OBSERVATION_DIM)
        active_mask: torch.Tensor,    # (capacity,) bool
        slot_block: torch.Tensor,     # (capacity, SLOT_DIM)
        hidden: torch.Tensor,         # (capacity, ACTOR_HIDDEN)
        noise: torch.Tensor,          # (capacity, ACTION_DIM)
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """One recurrent step.  Returns (actions, mean_kernel, new_hidden)."""
        slot_enc = torch.tanh(self.slot_encoder(slot_block))
        projected = torch.tanh(
            self.input_projector(torch.cat([observations, slot_enc], dim=1))
        )
        candidate = self.cell(projected, hidden)
        new_hidden = torch.where(active_mask[:, None], candidate, hidden)
        mean = self.action_head(new_hidden)
        actions = torch.tanh(mean + torch.exp(self.log_std) * noise)
        actions = torch.where(
            active_mask[:, None], actions, torch.zeros_like(actions)
        )
        return actions, mean, new_hidden


class EocivCritic(nn.Module):
    """The critic (registered contract 6.3; no privileged state)."""

    def __init__(self, actor_training_seed: int):
        super().__init__()
        layers = reg.CRITIC_CONTRACT["architecture"]["layers"]
        assert layers == (CRITIC_IN, 64, 64, 1)
        torch.manual_seed(int(actor_training_seed) + 500_000)
        self.body = nn.Sequential(
            nn.Linear(layers[0], layers[1]), nn.Tanh(),
            nn.Linear(layers[1], layers[2]), nn.Tanh(),
            nn.Linear(layers[2], layers[3]),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.body(features)


def critic_features(view: roster_env.CapacityRosterView, member_capacity: int) -> np.ndarray:
    """The registered critic read set: base critic state, active-set summary,
    pre-action lifecycle receipt counts.  Nothing else."""
    change = view.membership_change
    return np.concatenate([
        np.asarray(view.critic_state, dtype=np.float32),
        np.asarray([view.active_mask.sum() / member_capacity], dtype=np.float32),
        np.asarray(
            [len(change.joined), len(change.rejoined),
             len(change.temporarily_left), len(change.terminally_left)],
            dtype=np.float32,
        ),
    ])


class EocivValve(nn.Module):
    """The detached valve s_phi(W_minus) (registered contract 6.5).

    Reads ONLY the registered 9-feature extraction of the sealed W_minus
    bytes.  It shares no parameters with the actor or critic and never reads
    critic parameters at inference.
    """

    def __init__(self, actor_training_seed: int):
        super().__init__()
        layers = reg.VALVE_CONTRACT["architecture"]["layers"]
        assert layers == (VALVE_IN, 32, 32, 1)
        torch.manual_seed(int(actor_training_seed) + 700_000)
        self.body = nn.Sequential(
            nn.Linear(layers[0], layers[1]), nn.Tanh(),
            nn.Linear(layers[1], layers[2]), nn.Tanh(),
            nn.Linear(layers[2], layers[3]),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.body(features))

    def score(self, w_minus_bytes: bytes, member_capacity: int) -> float:
        features = torch.from_numpy(
            valve_features(w_minus_bytes, member_capacity)
        )
        with torch.no_grad():
            return float(self.forward(features[None, :])[0, 0])

    def decision(self, w_minus_bytes: bytes, member_capacity: int) -> bool:
        """The frozen inference rule D_L = 1{s_phi >= 1/4}; invalid opens."""
        try:
            value = self.score(w_minus_bytes, member_capacity)
        except Exception:
            return True  # HARD_OPEN
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            return True  # HARD_OPEN
        return value >= 0.25


def valve_features(w_minus_bytes: bytes, member_capacity: int) -> np.ndarray:
    """The registered 9-feature W_minus schema (contract 6.5), computed FROM
    the sealed bytes so the extraction is W_minus-measurable by construction."""
    record = json.loads(w_minus_bytes.decode("utf-8"))
    horizon = roster_env.HORIZON - 1
    return np.asarray(
        [
            record["time"] / horizon,
            record["load"],
            record["target_mix"],
            sum(record["active_mask"]) / member_capacity,
            record["receiver"]["spell_epoch"],
            record["receiver"]["opened_at"] / horizon,
            record["source"]["spell_epoch"],
            record["source"]["opened_at"] / horizon,
            1.0 if record["cell_class"] == "CRITICAL" else 0.0,
        ],
        dtype=np.float32,
    )


class ActorRunnerAdapter:
    """Drives ``EocivActor`` through the accepted ArmEpisodeRunner interface.

    Numpy in/out, torch.no_grad throughout (Stage 0 is forward-only).  The
    registered recurrent lifecycle is enforced here: fresh-join rows start at
    zeros (their hidden was never written while inactive), temporary leaves
    RETAIN hidden, rejoins restore it, and terminal leaves are zeroed at the
    terminal event boundary (contract 6.2).  The adapter counts steps to
    locate that boundary; the terminal-leave keys come from the pre-outcome
    ledger.
    """

    def __init__(self, actor: EocivActor, ledger):
        self.actor = actor
        self.capacity = int(ledger.member_capacity)
        self.terminal_leave = tuple(int(k) for k in ledger.terminal_leave)
        self._time = 0

    def initial_state(self) -> np.ndarray:
        self._time = 0
        return np.zeros((self.capacity, ACTOR_HIDDEN), dtype=np.float32)

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self._time == roster_env.EVENT_TIMES[2] and self.terminal_leave:
            hidden = hidden.copy()
            hidden[list(self.terminal_leave), :] = 0.0
        with torch.no_grad():
            actions, mean, new_hidden = self.actor.forward_step(
                torch.from_numpy(np.ascontiguousarray(observations, dtype=np.float32)),
                torch.from_numpy(np.ascontiguousarray(active_mask)),
                torch.from_numpy(np.ascontiguousarray(slot_block, dtype=np.float32)),
                torch.from_numpy(np.ascontiguousarray(hidden, dtype=np.float32)),
                torch.from_numpy(np.ascontiguousarray(noise, dtype=np.float32)),
            )
        self._time += 1
        return (
            actions.numpy().astype(np.float32),
            mean.numpy().astype(np.float32),
            new_hidden.numpy().astype(np.float32),
        )


def parameter_digest(*modules: nn.Module) -> str:
    """SHA-256 over all parameters in registration order (frozen-proof tool)."""
    h = hashlib.sha256()
    for module in modules:
        for name, parameter in sorted(module.named_parameters()):
            h.update(name.encode("ascii"))
            h.update(
                np.ascontiguousarray(
                    parameter.detach().numpy().astype(np.float32)
                ).tobytes()
            )
    return h.hexdigest()


def build_models(actor_training_seed: int) -> tuple[EocivActor, EocivCritic, EocivValve]:
    """Instantiate the three registered models for one actor seed."""
    configure_torch()
    actor = EocivActor(actor_training_seed)
    critic = EocivCritic(actor_training_seed)
    valve = EocivValve(actor_training_seed)
    return actor, critic, valve


def build_optimizers(actor: EocivActor, critic: EocivCritic, valve: EocivValve):
    """The registered optimizers (contracts 6.4 / 6.5).

    Stage 0 constructs them so their classes and constants are executable
    registration facts; NO step() call is licensed before Stage 1 (actor/
    critic) and Stage 2 (valve).
    """
    opt = reg.OPTIMIZATION
    actor_critic = torch.optim.Adam(
        list(actor.parameters()) + list(critic.parameters()),
        lr=opt["learning_rate"], betas=opt["betas"], eps=opt["eps"],
        weight_decay=opt["weight_decay"],
    )
    vopt = reg.VALVE_CONTRACT["optimizer"]
    valve_optimizer = torch.optim.Adam(
        valve.parameters(), lr=vopt["learning_rate"], betas=vopt["betas"],
        eps=vopt["eps"], weight_decay=vopt["weight_decay"],
    )
    return actor_critic, valve_optimizer
