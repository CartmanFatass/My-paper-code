"""Identity-free MAPR-4 and DIRECT-SET-AR structural/conformance surfaces.

The module has no random initializer.  Callers must supply explicit deterministic
parameter fixtures or, after separate authorization, an externally bound state.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Callable, Mapping, Sequence

import numpy as np


TOKEN_ROLES = ("EXEC_failed", "RELAY_failed", "EXEC_intact", "RELAY_intact")
AGENT_WIDTH, ZONE_WIDTH, GLOBAL_WIDTH = 38, 15, 4


def optimizer_contract() -> dict[str, object]:
    return {
        "schema": "VNFC-BPCR-R09-PPO-ADAMW-v1",
        "updates": 256, "episodes_per_update": 16, "decisions_per_episode": 6,
        "ppo_epochs": 4, "minibatches_per_epoch": 4, "records_per_minibatch": 24,
        "gamma": 1.0, "gae_lambda": 0.95, "clip": (0.8, 1.2),
        "value_coefficient": 0.5, "entropy_coefficient": 0.01,
        "learning_rate": 3e-4, "betas": (0.9, 0.999), "epsilon": 1e-8,
        "gradient_norm_cap": 0.5, "weight_decay": 1e-4,
        "decay_rule": "rank>=2 weights and embeddings only",
        "advantage_epsilon": None, "value_clipping": False, "kl_stop": False,
        "learning_rate_schedule": False, "checkpoint_selection": False,
    }


def strictness_witness() -> dict[str, object]:
    """Finite symbolic prefix-odds witness unavailable to MAPR's base scorer."""
    mapr_odds = {"prefix_a": 1.0, "prefix_b": 1.0}
    direct_odds = {"prefix_a": math.exp(1.0), "prefix_b": math.exp(-1.0)}
    return {
        "schema": "VNFC-BPCR-R09-DIRECT-STRICTNESS-WITNESS-v1",
        "same_state_and_remaining_candidates": True,
        "prefixes_differ_only_by_earlier_selected_pair": True,
        "mapr_conditional_odds": mapr_odds,
        "direct_conditional_odds": direct_odds,
        "strict": mapr_odds["prefix_a"] == mapr_odds["prefix_b"]
        and direct_odds["prefix_a"] != direct_odds["prefix_b"],
    }


def mapr_parameter_shapes() -> dict[str, tuple[int, ...]]:
    return {
        "agent.0.weight": (64, 38), "agent.0.bias": (64,),
        "agent.1.weight": (64, 64), "agent.1.bias": (64,),
        "zone.0.weight": (32, 15), "zone.0.bias": (32,),
        "zone.1.weight": (32, 32), "zone.1.bias": (32,),
        "global.0.weight": (16, 4), "global.0.bias": (16,),
        "global.1.weight": (16, 16), "global.1.bias": (16,),
        "token.embedding": (4, 16), "null.embedding": (64,),
        "score.0.weight": (128, 288), "score.0.bias": (128,),
        "score.1.weight": (64, 128), "score.1.bias": (64,),
        "score.out.weight": (1, 64), "score.out.bias": (1,),
        "critic.0.weight": (128, 208), "critic.0.bias": (128,),
        "critic.1.weight": (64, 128), "critic.1.bias": (64,),
        "critic.out.weight": (1, 64), "critic.out.bias": (1,),
    }


def direct_parameter_shapes() -> dict[str, tuple[int, ...]]:
    shapes = {f"base.{key}": shape for key, shape in mapr_parameter_shapes().items()}
    shapes.update({
        "residual.0.weight": (128, 400), "residual.0.bias": (128,),
        "residual.1.weight": (64, 128), "residual.1.bias": (64,),
        "residual.out.weight": (1, 64), "residual.out.bias": (1,),
    })
    return shapes


def validate_parameters(
    parameters: Mapping[str, np.ndarray], shapes: Mapping[str, tuple[int, ...]]
) -> None:
    if set(parameters) != set(shapes):
        raise ValueError("parameter names differ from the frozen structure")
    for name, shape in shapes.items():
        value = np.asarray(parameters[name])
        if value.shape != shape or value.dtype != np.float64 or not np.isfinite(value).all():
            raise ValueError(f"invalid deterministic parameter fixture: {name}")


def embed_mapr(parameters: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Exact containment embedding with an identically zero residual output."""
    validate_parameters(parameters, mapr_parameter_shapes())
    direct = {f"base.{name}": np.array(value, copy=True) for name, value in parameters.items()}
    for name, shape in direct_parameter_shapes().items():
        if name in direct:
            continue
        direct[name] = np.zeros(shape, dtype=np.float64)
    return direct


def exact_binary64_mean(rows: np.ndarray) -> np.ndarray:
    """Order-independent exact-rational sum followed by one binary64 division."""
    values = np.asarray(rows, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or not np.isfinite(values).all():
        raise ValueError("pooling requires one nonempty finite binary64 matrix")
    return np.array(
        [float(sum((Fraction.from_float(float(x)) for x in values[:, j]), Fraction()) / values.shape[0])
         for j in range(values.shape[1])],
        dtype=np.float64,
    )


def _silu(x: np.ndarray) -> np.ndarray:
    return x / (1.0 + np.exp(-x))


def _layer(x: np.ndarray, p: Mapping[str, np.ndarray], prefix: str, activate: bool) -> np.ndarray:
    y = p[f"{prefix}.weight"] @ x + p[f"{prefix}.bias"]
    return _silu(y) if activate else y


def _encoder(x: np.ndarray, p: Mapping[str, np.ndarray], prefix: str) -> np.ndarray:
    return _layer(_layer(x, p, f"{prefix}.0", True), p, f"{prefix}.1", True)


@dataclass(frozen=True)
class PublicObservation:
    agents: np.ndarray
    zones: np.ndarray
    globals: np.ndarray
    legal_masks: np.ndarray
    opaque_ranks: tuple[int, ...]
    fixed_token_occupants: tuple[int | None, ...] = (None, None, None, None)

    def validate(self) -> None:
        n = int(np.asarray(self.agents).shape[0])
        if np.asarray(self.agents).shape != (n, 38) or np.asarray(self.zones).shape != (2, 15):
            raise ValueError("observation tensor widths differ from revision 09")
        if np.asarray(self.globals).shape != (4,) or np.asarray(self.legal_masks).shape != (n, 4):
            raise ValueError("global or legality tensor shape differs")
        if len(self.opaque_ranks) != n or len(set(self.opaque_ranks)) != n:
            raise ValueError("opaque ranks must be a unique serialization-only total order")
        if len(self.fixed_token_occupants) != 4:
            raise ValueError("fixed token occupants must have width four")
        fixed = tuple(x for x in self.fixed_token_occupants if x is not None)
        if len(set(fixed)) != len(fixed) or any(x < 0 or x >= n for x in fixed):
            raise ValueError("fixed token occupants must be unique active row indices")
        for token, occupant in enumerate(self.fixed_token_occupants):
            if occupant is not None and np.any(np.asarray(self.legal_masks)[:, token] != 0):
                raise ValueError("a fixed en-route token has no learned candidate support")


@dataclass(frozen=True)
class EncodedObservation:
    agents: np.ndarray
    state208: np.ndarray
    token_embeddings: np.ndarray
    null_embedding: np.ndarray


def encode_mapr(observation: PublicObservation, parameters: Mapping[str, np.ndarray]) -> EncodedObservation:
    observation.validate(); validate_parameters(parameters, mapr_parameter_shapes())
    agents = np.stack([_encoder(row, parameters, "agent") for row in observation.agents])
    zones = np.concatenate([_encoder(row, parameters, "zone") for row in observation.zones])
    global_hidden = _encoder(observation.globals, parameters, "global")
    state = np.concatenate((exact_binary64_mean(agents), np.max(agents, axis=0), zones, global_hidden))
    if state.shape != (208,):
        raise AssertionError("public summary must have width 208")
    return EncodedObservation(
        agents=agents,
        state208=state,
        token_embeddings=np.asarray(parameters["token.embedding"]),
        null_embedding=np.asarray(parameters["null.embedding"]),
    )


def _base_hidden(encoded: EncodedObservation, candidate: int | None, token: int, p: Mapping[str, np.ndarray]) -> tuple[float, np.ndarray]:
    feature = encoded.null_embedding if candidate is None else encoded.agents[candidate]
    x = np.concatenate((feature, encoded.state208, encoded.token_embeddings[token]))
    if x.shape != (288,):
        raise AssertionError("MAPR scorer input must have width 288")
    h = _layer(_layer(x, p, "score.0", True), p, "score.1", True)
    return float(_layer(h, p, "score.out", False)[0]), h


def _softmax(logits: Sequence[float]) -> tuple[float, ...]:
    if not logits:
        raise ValueError("categorical support cannot be empty")
    top = max(logits); weights = [math.exp(x - top) for x in logits]; total = sum(weights)
    return tuple(x / total for x in weights)


@dataclass(frozen=True)
class TokenAudit:
    token: int
    candidates: tuple[int | None, ...]
    full_probabilities: tuple[float, ...]
    zero_residual_probabilities: tuple[float, ...]
    tv_distance: float


@dataclass(frozen=True)
class DecodedAudit:
    full_command: tuple[int | None, ...]
    zero_residual_command: tuple[int | None, ...]
    token_audits: tuple[TokenAudit, ...]
    i_res_active: int
    i_res_change: int


def _choice(candidates: Sequence[int | None], logits: Sequence[float], ranks: Sequence[int]) -> int | None:
    def key(index: int) -> tuple[float, int, int]:
        candidate = candidates[index]
        return (-float(logits[index]), ranks[candidate] if candidate is not None else 2**31-1, index)
    return candidates[min(range(len(candidates)), key=key)]


def decode_mapr(observation: PublicObservation, parameters: Mapping[str, np.ndarray]) -> tuple[int | None, ...]:
    encoded = encode_mapr(observation, parameters); available = set(range(len(observation.agents)))-{x for x in observation.fixed_token_occupants if x is not None}; command=[]
    for token in range(4):
        fixed=observation.fixed_token_occupants[token]
        if fixed is not None:
            command.append(fixed);continue
        candidates = tuple(i for i in sorted(available) if observation.legal_masks[i, token] == 1) + (None,)
        logits = tuple(_base_hidden(encoded, item, token, parameters)[0] for item in candidates)
        chosen = _choice(candidates, logits, observation.opaque_ranks); command.append(chosen)
        if chosen is not None: available.remove(chosen)
    return tuple(command)


def audit_direct(
    observation: PublicObservation, parameters: Mapping[str, np.ndarray]
) -> DecodedAudit:
    validate_parameters(parameters, direct_parameter_shapes())
    base = {name[5:]: value for name, value in parameters.items() if name.startswith("base.")}
    encoded = encode_mapr(observation, base); available = set(range(len(observation.agents)))-{x for x in observation.fixed_token_occupants if x is not None}
    prefix_sum = np.zeros(64); prefix_max = np.zeros(64); full_command=[]; zero_command=[]; audits=[]
    zero_available = set(available)
    for token in range(4):
        fixed=observation.fixed_token_occupants[token]
        if fixed is not None:
            full_command.append(fixed);zero_command.append(fixed);continue
        candidates = tuple(i for i in sorted(available) if observation.legal_masks[i, token] == 1) + (None,)
        base_pairs = tuple(_base_hidden(encoded, item, token, base) for item in candidates)
        residuals=[]
        for _, hidden in base_pairs:
            x=np.concatenate((encoded.state208,hidden,prefix_sum,prefix_max))
            h=_layer(_layer(x,parameters,"residual.0",True),parameters,"residual.1",True)
            residuals.append(float(_layer(h,parameters,"residual.out",False)[0]))
        zero_logits=tuple(item[0] for item in base_pairs); full_logits=tuple(x+r for x,r in zip(zero_logits,residuals))
        full_probs=_softmax(full_logits);zero_probs=_softmax(zero_logits)
        chosen=_choice(candidates,full_logits,observation.opaque_ranks);full_command.append(chosen)
        zero_candidates=tuple(i for i in sorted(zero_available) if observation.legal_masks[i,token]==1)+(None,)
        zero_logits_decode=tuple(_base_hidden(encoded,item,token,base)[0] for item in zero_candidates)
        zero_chosen=_choice(zero_candidates,zero_logits_decode,observation.opaque_ranks);zero_command.append(zero_chosen)
        audits.append(TokenAudit(token,candidates,full_probs,zero_probs,0.5*sum(abs(a-b) for a,b in zip(full_probs,zero_probs))))
        if chosen is not None:
            available.remove(chosen); _, hidden=_base_hidden(encoded,chosen,token,base);prefix_sum+=hidden;prefix_max=hidden if len(full_command)==1 else np.maximum(prefix_max,hidden)
        if zero_chosen is not None: zero_available.remove(zero_chosen)
    full=tuple(full_command);zero=tuple(zero_command)
    return DecodedAudit(full,zero,tuple(audits),int(any(a.tv_distance>=0.05 for a in audits)),int(full!=zero))
