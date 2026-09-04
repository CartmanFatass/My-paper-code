"""Source-owned scalar MAPR/DIRECT reference surface for VNFC R02 A0.

The implementation canonicalizes physical entities before the first numeric
operation.  It intentionally evaluates one row and one candidate at a time.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Protocol, Sequence

from .fixtures import MAPR_PARAMETER_SHAPES, ParameterFixture


class ModelError(ValueError):
    pass


class Kernel(Protocol):
    def sigmoid_R02(self, value: float) -> float: ...
    def exp_R02(self, value: float) -> float: ...
    def log_R02(self, value: float) -> float: ...
    def sqrt_R02(self, value: float) -> float: ...


@dataclass(frozen=True)
class PublicObservation:
    """One externally presented public state.

    Fixed occupants are physical entity handles, not transient row indices.
    """

    entity_handles: tuple[int, ...]
    agents: tuple[tuple[float, ...], ...]
    zones: tuple[tuple[float, ...], tuple[float, ...]]
    global_row: tuple[float, ...]
    legal: tuple[tuple[bool, bool, bool, bool], ...]
    opaque_ranks: tuple[int, ...]
    fixed_occupants: tuple[int | None, int | None, int | None, int | None]

    def validate(self) -> None:
        n = len(self.entity_handles)
        if not n or len(set(self.entity_handles)) != n:
            raise ModelError("physical entity handles must be unique")
        if len(self.agents) != n or any(len(row) != 38 for row in self.agents):
            raise ModelError("agent public rows differ from width 38")
        if len(self.zones) != 2 or any(len(row) != 15 for row in self.zones):
            raise ModelError("zone rows differ from width 15")
        if len(self.global_row) != 4 or len(self.legal) != n or any(len(row) != 4 for row in self.legal):
            raise ModelError("global or legality width differs")
        if len(self.opaque_ranks) != n or len(set(self.opaque_ranks)) != n or min(self.opaque_ranks) < 1:
            raise ModelError("opaque ranks must be a positive unique total order")
        fixed = tuple(item for item in self.fixed_occupants if item is not None)
        if len(fixed) != len(set(fixed)) or not set(fixed).issubset(self.entity_handles):
            raise ModelError("fixed occupants must be unique active physical handles")
        for token, occupant in enumerate(self.fixed_occupants):
            if occupant is not None and any(row[token] for row in self.legal):
                raise ModelError("fixed tokens cannot expose learned legality")
        if not all(math.isfinite(value) for row in self.agents for value in row):
            raise ModelError("agent rows must be finite")
        if not all(math.isfinite(value) for row in self.zones for value in row) or not all(math.isfinite(value) for value in self.global_row):
            raise ModelError("public state must be finite")


@dataclass(frozen=True)
class CanonicalObservation:
    entity_handles: tuple[int, ...]
    agents: tuple[tuple[float, ...], ...]
    zones: tuple[tuple[float, ...], tuple[float, ...]]
    global_row: tuple[float, ...]
    legal: tuple[tuple[bool, bool, bool, bool], ...]
    opaque_ranks: tuple[int, ...]
    fixed_indices: tuple[int | None, int | None, int | None, int | None]
    inverse_by_opaque_rank: tuple[tuple[int, int], ...]

    def canonical_bytes(self) -> bytes:
        body = {
            "entity_handles": self.entity_handles,
            "agents": tuple(tuple(value.hex() for value in row) for row in self.agents),
            "zones": tuple(tuple(value.hex() for value in row) for row in self.zones),
            "global": tuple(value.hex() for value in self.global_row),
            "legal": self.legal,
            "opaque_ranks": self.opaque_ranks,
            "fixed_indices": self.fixed_indices,
            "inverse": self.inverse_by_opaque_rank,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


@dataclass(frozen=True)
class EncodedState:
    agents: tuple[tuple[float, ...], ...]
    state208: tuple[float, ...]
    token_embeddings: tuple[tuple[float, ...], ...]
    null_embedding: tuple[float, ...]


@dataclass(frozen=True)
class CandidateTrace:
    candidate: int | None
    opaque_rank: int | None
    base_logit: float
    final_logit: float
    base_hidden: tuple[float, ...]
    residual_hidden: tuple[float, ...] | None


@dataclass(frozen=True)
class TokenTrace:
    token: int
    fixed: bool
    support: tuple[int | None, ...]
    candidates: tuple[CandidateTrace, ...]
    probability: object | None
    deterministic_command: int | None
    selected_command: int | None
    selected_opaque_rank: int | None
    log_probability: float
    entropy: float
    action_word: int | None
    prefix_sum_before: tuple[float, ...]
    prefix_max_before: tuple[float, ...]
    prefix_sum_after: tuple[float, ...]
    prefix_max_after: tuple[float, ...]


@dataclass(frozen=True)
class ForwardTrace:
    arm: str
    canonical_sha256: str
    canonical: CanonicalObservation
    tokens: tuple[TokenTrace, ...]
    physical_command: tuple[int | None, ...]
    physical_opaque_command: tuple[int | None, ...]
    joint_log_probability: float
    value: float


@dataclass(frozen=True)
class ReplayResult:
    new_logp: float
    old_logp: float
    ratio: float
    actor: float
    value_loss: float
    mean_entropy: float
    total_loss: float
    trace: ForwardTrace


def canonicalize(observation: PublicObservation) -> CanonicalObservation:
    observation.validate()
    order = tuple(sorted(range(len(observation.entity_handles)), key=lambda index: observation.opaque_ranks[index]))
    handles = tuple(observation.entity_handles[index] for index in order)
    ranks = tuple(observation.opaque_ranks[index] for index in order)
    handle_to_index = {handle: index for index, handle in enumerate(handles)}
    fixed = tuple(None if handle is None else handle_to_index[handle] for handle in observation.fixed_occupants)
    return CanonicalObservation(
        handles,
        tuple(observation.agents[index] for index in order),
        observation.zones,
        observation.global_row,
        tuple(observation.legal[index] for index in order),
        ranks,
        fixed,  # type: ignore[arg-type]
        tuple((rank, handle) for rank, handle in zip(ranks, handles)),
    )


class _Parameters:
    def __init__(self, fixture: ParameterFixture, arm: str):
        if fixture.arm != arm:
            raise ModelError("fixture arm differs")
        self._rows = fixture.by_name()

    def row(self, name: str) -> tuple[float, ...]:
        try:
            return self._rows[name].values
        except KeyError as error:
            raise ModelError(f"parameter absent: {name}") from error

    def shape(self, name: str) -> tuple[int, ...]:
        return self._rows[name].shape

    def matrix(self, name: str) -> tuple[tuple[float, ...], ...]:
        shape = self.shape(name)
        if len(shape) != 2:
            raise ModelError("matrix parameter expected")
        values = self.row(name)
        return tuple(tuple(values[row * shape[1]:(row + 1) * shape[1]]) for row in range(shape[0]))


def _rn64(value: float) -> float:
    from .scalar import rn64
    return rn64(value)


def _add(left: float, right: float) -> float:
    return _rn64(_rn64(left) + _rn64(right))


def _mul(left: float, right: float) -> float:
    return _rn64(_rn64(left) * _rn64(right))


def _affine(values: Sequence[float], weights: Sequence[Sequence[float]], bias: Sequence[float]) -> tuple[float, ...]:
    if len(weights) != len(bias) or any(len(row) != len(values) for row in weights):
        raise ModelError("affine shape differs")
    outputs = []
    for row, start in zip(weights, bias):
        total = _rn64(start)
        for weight, value in zip(row, values):
            total = _add(total, _mul(weight, value))
        outputs.append(0.0 if total == 0.0 else total)
    return tuple(outputs)


def _silu(value: float, kernel: Kernel) -> float:
    result = _mul(value, kernel.sigmoid_R02(value))
    return 0.0 if result == 0.0 else result


def _layer(values: Sequence[float], p: _Parameters, prefix: str, kernel: Kernel, activate: bool = True) -> tuple[float, ...]:
    output = _affine(values, p.matrix(f"{prefix}.weight"), p.row(f"{prefix}.bias"))
    return tuple(_silu(value, kernel) for value in output) if activate else output


def _encoder(values: Sequence[float], p: _Parameters, prefix: str, kernel: Kernel) -> tuple[float, ...]:
    return _layer(_layer(values, p, f"{prefix}.0", kernel), p, f"{prefix}.1", kernel)


def _exact_mean(rows: Sequence[Sequence[float]]) -> tuple[float, ...]:
    from .scalar import exact_roster_mean
    return tuple(exact_roster_mean(rows))


def _strict_max(rows: Sequence[Sequence[float]]) -> tuple[float, ...]:
    from .scalar import strict_roster_max
    result = strict_roster_max(rows)
    return tuple(result[0])


def encode(canonical: CanonicalObservation, parameters: ParameterFixture, arm: str, kernel: Kernel) -> EncodedState:
    p = _Parameters(parameters, arm)
    base_prefix = "" if arm == "MAPR" else "base."
    agents = tuple(_encoder(row, p, f"{base_prefix}agent", kernel) for row in canonical.agents)
    zones = tuple(_encoder(row, p, f"{base_prefix}zone", kernel) for row in canonical.zones)
    global_hidden = _encoder(canonical.global_row, p, f"{base_prefix}global", kernel)
    state = _exact_mean(agents) + _strict_max(agents) + zones[0] + zones[1] + global_hidden
    if len(state) != 208:
        raise AssertionError("encoded public state width differs")
    token_values = p.row(f"{base_prefix}token.embedding")
    token_embeddings = tuple(tuple(token_values[token * 16:(token + 1) * 16]) for token in range(4))
    return EncodedState(agents, state, token_embeddings, p.row(f"{base_prefix}null.embedding"))


def _base_candidate(encoded: EncodedState, candidate: int | None, token: int, p: _Parameters, arm: str, kernel: Kernel) -> tuple[float, tuple[float, ...]]:
    prefix = "" if arm == "MAPR" else "base."
    feature = encoded.null_embedding if candidate is None else encoded.agents[candidate]
    hidden = _layer(_layer(feature + encoded.state208 + encoded.token_embeddings[token], p, f"{prefix}score.0", kernel), p, f"{prefix}score.1", kernel)
    return _layer(hidden, p, f"{prefix}score.out", kernel, False)[0], hidden


def _positive_zero_output(p: _Parameters) -> bool:
    import struct
    zero = struct.pack(">d", 0.0)
    return all(struct.pack(">d", value) == zero for name in ("residual.out.weight", "residual.out.bias") for value in p.row(name))


def _direct_residual(encoded: EncodedState, hidden: tuple[float, ...], prefix_sum: tuple[float, ...], prefix_max: tuple[float, ...], p: _Parameters, kernel: Kernel) -> tuple[float, tuple[float, ...]]:
    residual_hidden = _layer(_layer(encoded.state208 + hidden + prefix_sum + prefix_max, p, "residual.0", kernel), p, "residual.1", kernel)
    return _layer(residual_hidden, p, "residual.out", kernel, False)[0], residual_hidden


def _probability(logits: Sequence[float], candidates: Sequence[int | None], kernel: Kernel) -> object:
    from .probability import construct_probability
    return construct_probability(tuple(logits), tuple(candidates), kernel)


def _prob_field(probability: object, *names: str) -> object:
    for name in names:
        if hasattr(probability, name):
            return getattr(probability, name)
    raise ModelError(f"probability object lacks {names}")


def _deterministic(probability: object) -> int | None:
    from .probability import deterministic_choice
    return deterministic_choice(probability)


def _production(probability: object, word: int) -> int | None:
    from .probability import choose_production_word
    return choose_production_word(probability, word)


def _choice_index(probability: object, chosen: int | None) -> int:
    candidates = tuple(_prob_field(probability, "candidates"))
    try:
        return candidates.index(chosen)
    except ValueError as error:
        raise ModelError("forced physical command is outside support") from error


def _probabilities(probability: object) -> tuple[float, ...]:
    return tuple(_prob_field(probability, "probabilities", "p"))


def _probability_entropy(probability: object, kernel: Kernel) -> float:
    return float(_prob_field(probability, "stored_H"))


def _log_probability(probability: object, chosen: int | None, kernel: Kernel) -> float:
    return float(tuple(_prob_field(probability, "stored_log_p"))[_choice_index(probability, chosen)])


def _critic(encoded: EncodedState, p: _Parameters, arm: str, kernel: Kernel) -> float:
    prefix = "" if arm == "MAPR" else "base."
    hidden = _layer(_layer(encoded.state208, p, f"{prefix}critic.0", kernel), p, f"{prefix}critic.1", kernel)
    return _layer(hidden, p, f"{prefix}critic.out", kernel, False)[0]


def forward(
    observation: PublicObservation,
    parameters: ParameterFixture,
    arm: str,
    kernel: Kernel,
    *,
    action_words: Sequence[int] | None = None,
    forced_physical_command: Sequence[int | None] | None = None,
) -> ForwardTrace:
    if arm not in ("MAPR", "DIRECT") or parameters.arm != arm:
        raise ModelError("model arm differs")
    if action_words is not None and len(action_words) != 4:
        raise ModelError("action-word vector must have four token coordinates")
    if forced_physical_command is not None and len(forced_physical_command) != 4:
        raise ModelError("forced physical command must have four tokens")
    canonical = canonicalize(observation)
    p = _Parameters(parameters, arm)
    encoded = encode(canonical, parameters, arm, kernel)
    available = set(range(len(canonical.entity_handles))) - {item for item in canonical.fixed_indices if item is not None}
    prefix_sum = (0.0,) * 64
    prefix_max = (0.0,) * 64
    prefix_has = False
    token_rows: list[TokenTrace] = []
    physical_command: list[int | None] = []
    opaque_command: list[int | None] = []
    joint_logp = 0.0
    zero_output = arm == "DIRECT" and _positive_zero_output(p)
    for token in range(4):
        before_sum, before_max = prefix_sum, prefix_max
        fixed = canonical.fixed_indices[token]
        if fixed is not None:
            from .probability import construct_fixed_probability
            handle = canonical.entity_handles[fixed]
            rank = canonical.opaque_ranks[fixed]
            fixed_probability = construct_fixed_probability(rank)
            candidate = CandidateTrace(rank, rank, 0.0, 0.0, encoded.agents[fixed], None)
            token_rows.append(TokenTrace(token, True, (rank,), (candidate,), fixed_probability, handle, handle, rank, 0.0, 0.0, None, before_sum, before_max, prefix_sum, prefix_max))
            physical_command.append(handle); opaque_command.append(rank)
            continue
        support_indices = tuple(index for index in sorted(available) if canonical.legal[index][token])
        support = tuple(canonical.opaque_ranks[index] for index in support_indices) + (None,)
        candidate_rows = []
        logits = []
        for candidate_index in support_indices + (None,):
            base_logit, base_hidden = _base_candidate(encoded, candidate_index, token, p, arm, kernel)
            residual_hidden = None
            final_logit = base_logit
            if arm == "DIRECT":
                residual, residual_hidden = _direct_residual(encoded, base_hidden, prefix_sum, prefix_max, p, kernel)
                final_logit = base_logit if zero_output else _add(base_logit, residual)
            logits.append(final_logit)
            rank = None if candidate_index is None else canonical.opaque_ranks[candidate_index]
            candidate_rows.append(CandidateTrace(rank, rank, base_logit, final_logit, base_hidden, residual_hidden))
        probability = _probability(logits, support, kernel)
        deterministic_rank = _deterministic(probability)
        rank_to_index = {rank: index for index, rank in enumerate(canonical.opaque_ranks)}
        deterministic_index = None if deterministic_rank is None else rank_to_index[deterministic_rank]
        deterministic_handle = None if deterministic_index is None else canonical.entity_handles[deterministic_index]
        if forced_physical_command is not None:
            forced_handle = forced_physical_command[token]
            if forced_handle is None:
                chosen_rank = None
            else:
                try:
                    chosen_index = canonical.entity_handles.index(forced_handle)
                except ValueError as error:
                    raise ModelError("forced command names an inactive physical entity") from error
                chosen_rank = canonical.opaque_ranks[chosen_index]
            _choice_index(probability, chosen_rank)
            word = None if action_words is None else action_words[token]
        elif action_words is None:
            chosen_rank = deterministic_rank
            word = None
        else:
            word = action_words[token]
            chosen_rank = _production(probability, word)
        chosen = None if chosen_rank is None else rank_to_index[chosen_rank]
        handle = None if chosen is None else canonical.entity_handles[chosen]
        rank = None if chosen is None else canonical.opaque_ranks[chosen]
        logp = _log_probability(probability, chosen_rank, kernel)
        entropy = _probability_entropy(probability, kernel)
        joint_logp = _add(joint_logp, logp)
        if chosen is not None:
            available.remove(chosen)
            chosen_hidden = candidate_rows[support.index(chosen_rank)].base_hidden
            from .scalar import update_prefix
            prefix_sum, prefix_max, prefix_has = update_prefix(
                prefix_sum, prefix_max, chosen_hidden,
                max_has_value=prefix_has, variable=True, selected_null=False,
            )
        token_rows.append(TokenTrace(token, False, support, tuple(candidate_rows), probability, deterministic_handle, handle, rank, logp, entropy, word, before_sum, before_max, prefix_sum, prefix_max))
        physical_command.append(handle); opaque_command.append(rank)
    return ForwardTrace(
        arm=arm,
        canonical_sha256=hashlib.sha256(canonical.canonical_bytes()).hexdigest(),
        canonical=canonical,
        tokens=tuple(token_rows),
        physical_command=tuple(physical_command),
        physical_opaque_command=tuple(opaque_command),
        joint_log_probability=joint_logp,
        value=_critic(encoded, p, arm, kernel),
    )


def forced_replay(
    observation: PublicObservation,
    parameters: ParameterFixture,
    arm: str,
    kernel: Kernel,
    *,
    physical_command: Sequence[int | None],
    old_logp: float,
) -> ReplayResult:
    trace = forward(observation, parameters, arm, kernel, forced_physical_command=physical_command)
    delta = _rn64(trace.joint_log_probability - old_logp)
    ratio = kernel.exp_R02(delta)
    unclipped = _mul(ratio, 1.0)
    clipped_ratio = min(max(ratio, float.fromhex("0x1.999999999999ap-1")), float.fromhex("0x1.3333333333333p+0"))
    clipped = _mul(clipped_ratio, 1.0)
    actor = _rn64(-min(unclipped, clipped))
    residual = _rn64(trace.value - 0.25)
    value_loss = _mul(residual, residual)
    entropy_sum = 0.0
    for token in trace.tokens:
        if not token.fixed:
            entropy_sum = _add(entropy_sum, token.entropy)
    mean_entropy = _rn64(entropy_sum / 4.0)
    total = _rn64(_add(actor, _mul(0.5, value_loss)) - _mul(0.01, mean_entropy))
    return ReplayResult(trace.joint_log_probability, old_logp, ratio, actor, value_loss, mean_entropy, total, trace)


def containment_predicates(mapr: ForwardTrace, direct: ForwardTrace) -> dict[str, bool]:
    if mapr.canonical_sha256 != direct.canonical_sha256:
        raise ModelError("containment traces use different canonical states")
    return {
        "base_logits_equal": tuple(tuple(row.base_logit for row in token.candidates) for token in mapr.tokens) == tuple(tuple(row.base_logit for row in token.candidates) for token in direct.tokens),
        "final_logits_equal": tuple(tuple(row.final_logit for row in token.candidates) for token in mapr.tokens) == tuple(tuple(row.final_logit for row in token.candidates) for token in direct.tokens),
        "physical_command_equal": mapr.physical_command == direct.physical_command,
        "opaque_command_equal": mapr.physical_opaque_command == direct.physical_opaque_command,
        "joint_log_probability_equal": mapr.joint_log_probability.hex() == direct.joint_log_probability.hex(),
        "value_equal": mapr.value.hex() == direct.value.hex(),
        "entropy_equal": tuple(token.entropy.hex() for token in mapr.tokens) == tuple(token.entropy.hex() for token in direct.tokens),
    }


def trace_fingerprint(trace: ForwardTrace) -> str:
    body = {
        "arm": trace.arm,
        "canonical": trace.canonical_sha256,
        "physical_command": trace.physical_command,
        "opaque_command": trace.physical_opaque_command,
        "joint_logp": trace.joint_log_probability.hex(),
        "value": trace.value.hex(),
        "tokens": [
            {
                "fixed": token.fixed,
                "support": token.support,
                "base": [row.base_logit.hex() for row in token.candidates],
                "final": [row.final_logit.hex() for row in token.candidates],
                "logp": token.log_probability.hex(),
                "entropy": token.entropy.hex(),
                "command": token.selected_command,
                "opaque": token.selected_opaque_rank,
            }
            for token in trace.tokens
        ],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class ExactSyntheticStep:
    replay: ReplayResult
    raw_gradients: tuple[object, ...]
    raw_base_gradients: tuple[object, ...]
    clipped_gradients: tuple[object, ...]
    updated_parameters: tuple[object, ...]
    optimizer_state: object
    node_table_sha256: str
    raw_gradient_sha256: str
    clipped_gradient_sha256: str
    optimizer_sha256: str


def _parameter_tensors(fixture: ParameterFixture) -> tuple[object, ...]:
    from .optimizer import ParameterTensor
    return tuple(ParameterTensor(row.name, row.shape, row.values) for row in sorted(fixture.tensors, key=lambda item: item.name))


def _tensor_digest(rows: Sequence[object]) -> str:
    body = [
        {
            "name": getattr(row, "name"),
            "shape": list(getattr(row, "shape")),
            "values": [value.hex() for value in getattr(row, "values")],
        }
        for row in rows
    ]
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def _state_digest(state: object) -> str:
    return hashlib.sha256(json.dumps(getattr(state, "to_dict")(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def _scalar_matrix(values: Sequence[object], shape: tuple[int, ...]) -> tuple[tuple[object, ...], ...]:
    if len(shape) != 2:
        raise ModelError("scalar parameter matrix expected")
    return tuple(tuple(values[row * shape[1]:(row + 1) * shape[1]]) for row in range(shape[0]))


def exact_synthetic_step(
    observation: PublicObservation,
    parameters: ParameterFixture,
    arm: str,
    kernel: Kernel,
    *,
    physical_command: Sequence[int | None],
    old_logp: float,
    optimizer_state: object | None = None,
) -> ExactSyntheticStep:
    """Construct the complete frozen scalar forward/loss/reverse/AdamW graph.

    The environment command and old log probability must come from the group's
    canonical collection.  This function mutates no fixture or optimizer input.
    """
    from .autodiff import ScalarTape
    from .optimizer import adamw_step, initialize_adamw
    from .probability import construct_probability

    if arm not in ("MAPR", "DIRECT") or parameters.arm != arm:
        raise ModelError("exact synthetic step arm differs")
    canonical = canonicalize(observation)
    parameter_tensors = _parameter_tensors(parameters)
    tape = ScalarTape(kernel)
    leaves = tape.register_parameters(parameter_tensors)

    auxiliary: dict[str, float] = {}
    for row, values in enumerate(canonical.agents):
        for column, value in enumerate(values):
            auxiliary[f"input/agent/{row}/{column}"] = value
    for row, values in enumerate(canonical.zones):
        for column, value in enumerate(values):
            auxiliary[f"input/zone/{row}/{column}"] = value
    for column, value in enumerate(canonical.global_row):
        auxiliary[f"input/global/{column}"] = value
    constants = {
        "loss/constant/advantage": 1.0,
        "loss/constant/clip_lower": float.fromhex("0x1.999999999999ap-1"),
        "loss/constant/clip_upper": float.fromhex("0x1.3333333333333p+0"),
        "loss/constant/entropy_coefficient": float.fromhex("0x1.47ae147ae147bp-7"),
        "loss/constant/old_logp": old_logp,
        "loss/constant/target": 0.25,
        "loss/constant/token_count": 4.0,
        "loss/constant/value_coefficient": 0.5,
        "prefix/initial/max/has": 0.0,
    }
    for index in range(64):
        constants[f"prefix/initial/max/{index}"] = 0.0
        constants[f"prefix/initial/sum/{index}"] = 0.0
    # Fixed-token and empty categorical values are leaves so no primitive is
    # emitted without a path to the final loss root.
    for token in range(4):
        constants[f"token/{token}/fixed/entropy"] = 0.0
        constants[f"token/{token}/fixed/logp"] = 0.0
    aux_nodes: dict[str, object] = {}
    for path in sorted({**auxiliary, **constants}):
        value = auxiliary[path] if path in auxiliary else constants[path]
        aux_nodes[path] = tape.constant(path, value)

    def parameter_name(name: str) -> str:
        return name if arm == "MAPR" else f"base.{name}"

    def layer(inputs: Sequence[object], prefix: str, path: str, activate: bool = True) -> tuple[object, ...]:
        weight_name = f"{prefix}.weight"
        bias_name = f"{prefix}.bias"
        shape = parameters.by_name()[weight_name].shape
        weights = _scalar_matrix(leaves[weight_name], shape)
        output = tape.affine(inputs, weights, leaves[bias_name], f"{path}/affine")
        return tuple(tape.silu(value, f"{path}/silu/{j}") for j, value in enumerate(output)) if activate else output

    def encoder(inputs: Sequence[object], prefix: str, path: str) -> tuple[object, ...]:
        return layer(layer(inputs, f"{prefix}.0", f"{path}/layer0"), f"{prefix}.1", f"{path}/layer1")

    base = "" if arm == "MAPR" else "base."
    agent_nodes = tuple(
        tuple(aux_nodes[f"input/agent/{row}/{column}"] for column in range(38))
        for row in range(len(canonical.agents))
    )
    zone_nodes = tuple(tuple(aux_nodes[f"input/zone/{row}/{column}"] for column in range(15)) for row in range(2))
    global_nodes = tuple(aux_nodes[f"input/global/{column}"] for column in range(4))
    encoded_agents = tuple(encoder(row, f"{base}agent", f"encode/agent/{index}") for index, row in enumerate(agent_nodes))
    encoded_zones = tuple(encoder(row, f"{base}zone", f"encode/zone/{index}") for index, row in enumerate(zone_nodes))
    encoded_global = encoder(global_nodes, f"{base}global", "encode/global")
    state = tape.roster_mean(encoded_agents, "encode/roster_mean") + tape.roster_max(encoded_agents, "encode/roster_max") + encoded_zones[0] + encoded_zones[1] + encoded_global
    token_embedding = leaves[f"{base}token.embedding"]
    null_embedding = leaves[f"{base}null.embedding"]

    def base_candidate(candidate_index: int | None, token: int, path: str) -> tuple[object, tuple[object, ...]]:
        feature = null_embedding if candidate_index is None else encoded_agents[candidate_index]
        embedding = token_embedding[token * 16:(token + 1) * 16]
        hidden = layer(layer(feature + state + embedding, f"{base}score.0", f"{path}/score0"), f"{base}score.1", f"{path}/score1")
        logit = layer(hidden, f"{base}score.out", f"{path}/score_out", False)[0]
        return logit, hidden

    available = set(range(len(canonical.entity_handles))) - {item for item in canonical.fixed_indices if item is not None}
    prefix_sum_nodes = tuple(aux_nodes[f"prefix/initial/sum/{index}"] for index in range(64))
    prefix_max_nodes = tuple(aux_nodes[f"prefix/initial/max/{index}"] for index in range(64))
    prefix_has = False
    logp_nodes: list[object] = []
    entropy_specs: list[tuple[object, object, int] | object] = []
    zero_output = arm == "DIRECT" and _positive_zero_output(_Parameters(parameters, arm))
    rank_to_index = {rank: index for index, rank in enumerate(canonical.opaque_ranks)}
    if len(physical_command) != 4:
        raise ModelError("synthetic forced command width differs")
    for token in range(4):
        fixed = canonical.fixed_indices[token]
        if fixed is not None:
            expected = canonical.entity_handles[fixed]
            if physical_command[token] != expected:
                raise ModelError("forced fixed physical command differs")
            logp_nodes.append(aux_nodes[f"token/{token}/fixed/logp"])
            entropy_specs.append(aux_nodes[f"token/{token}/fixed/entropy"])
            continue
        support_indices = tuple(index for index in sorted(available) if canonical.legal[index][token])
        support_ranks = tuple(canonical.opaque_ranks[index] for index in support_indices) + (None,)
        logits: list[object] = []
        hidden_by_rank: dict[int | None, tuple[object, ...]] = {}
        for candidate_index in support_indices + (None,):
            rank = None if candidate_index is None else canonical.opaque_ranks[candidate_index]
            candidate_path = f"token/{token}/candidate/{'NULL' if rank is None else rank}"
            base_logit, hidden = base_candidate(candidate_index, token, candidate_path)
            final_logit = base_logit
            if arm == "DIRECT":
                residual_input = state + hidden + prefix_sum_nodes + prefix_max_nodes
                residual_hidden = layer(layer(residual_input, "residual.0", f"{candidate_path}/residual0"), "residual.1", f"{candidate_path}/residual1")
                residual = layer(residual_hidden, "residual.out", f"{candidate_path}/residual_out", False)[0]
                final_logit = tape.identity_join(base_logit, residual, f"{candidate_path}/identity_join") if zero_output else tape.add(base_logit, residual, f"{candidate_path}/residual_add")
            logits.append(final_logit)
            hidden_by_rank[rank] = hidden
        probability = construct_probability(tuple(node.value for node in logits), support_ranks, kernel)
        q = tape.centered_clamp(logits, probability, f"token/{token}/centered")
        stored = tape.stored_categorical(probability)
        handle = physical_command[token]
        if handle is None:
            chosen_rank = None
        else:
            try:
                chosen_rank = canonical.opaque_ranks[canonical.entity_handles.index(handle)]
            except ValueError as error:
                raise ModelError("forced command names inactive entity") from error
        if chosen_rank not in support_ranks:
            raise ModelError("forced command is outside canonical support")
        logp_nodes.append(tape.categorical_log_probability(q, stored, chosen_rank, f"token/{token}/logp"))
        entropy_specs.append((q, stored, token))
        if chosen_rank is not None:
            chosen_index = rank_to_index[chosen_rank]
            available.remove(chosen_index)
            # Prefix after the final variable token is not part of the loss DAG.
            future_variable = any(canonical.fixed_indices[later] is None for later in range(token + 1, 4))
            if arm == "DIRECT" and future_variable:
                chosen_hidden = hidden_by_rank[chosen_rank]
                prefix_sum_nodes = tuple(tape.add(left, right, f"token/{token}/prefix/sum/{index}") for index, (left, right) in enumerate(zip(prefix_sum_nodes, chosen_hidden)))
                if prefix_has:
                    prefix_max_nodes = tuple(tape.strict_max((left, right), f"token/{token}/prefix/max/{index}") for index, (left, right) in enumerate(zip(prefix_max_nodes, chosen_hidden)))
                else:
                    prefix_max_nodes = tuple(tape.copy(value, f"token/{token}/prefix/max/{index}") for index, value in enumerate(chosen_hidden))
                prefix_has = True

    new_logp_node = logp_nodes[0]
    for token, node in enumerate(logp_nodes[1:], start=1):
        new_logp_node = tape.add(new_logp_node, node, f"loss/logp_sum/{token}")
    delta = tape.sub(new_logp_node, aux_nodes["loss/constant/old_logp"], "loss/logp_delta")
    ratio = tape.exp(delta, "loss/ratio")
    unclipped = tape.mul(ratio, aux_nodes["loss/constant/advantage"], "loss/unclipped_actor_term")
    clipped_ratio = tape.clamp(ratio, float.fromhex("0x1.999999999999ap-1"), float.fromhex("0x1.3333333333333p+0"), "loss/clipped_ratio")
    clipped = tape.mul(clipped_ratio, aux_nodes["loss/constant/advantage"], "loss/clipped_actor_term")
    actor = tape.neg(tape.minimum(unclipped, clipped, "loss/actor_minimum"), "loss/actor")
    critic_hidden = layer(layer(state, f"{base}critic.0", "critic/layer0"), f"{base}critic.1", "critic/layer1")
    value_node = layer(critic_hidden, f"{base}critic.out", "critic/out", False)[0]
    value_residual = tape.sub(value_node, aux_nodes["loss/constant/target"], "loss/value_residual")
    value_square = tape.mul(value_residual, value_residual, "loss/value_square")
    scaled_value = tape.mul(aux_nodes["loss/constant/value_coefficient"], value_square, "loss/scaled_value")
    actor_value = tape.add(actor, scaled_value, "loss/actor_plus_value")
    entropy_nodes = [
        spec if not isinstance(spec, tuple) else tape.categorical_entropy(spec[0], spec[1], f"token/{spec[2]}/entropy")
        for spec in entropy_specs
    ]
    entropy_sum = entropy_nodes[0]
    for token, node in enumerate(entropy_nodes[1:], start=1):
        entropy_sum = tape.add(entropy_sum, node, f"loss/entropy_sum/{token}")
    mean_entropy = tape.div(entropy_sum, aux_nodes["loss/constant/token_count"], "loss/mean_entropy")
    scaled_entropy = tape.mul(aux_nodes["loss/constant/entropy_coefficient"], mean_entropy, "loss/scaled_entropy")
    total = tape.sub(actor_value, scaled_entropy, "loss/total")
    backward = tape.backward(total)
    state_before = initialize_adamw(parameter_tensors) if optimizer_state is None else optimizer_state
    step = adamw_step(parameter_tensors, backward.parameter_gradients, state_before, kernel)
    replay = forced_replay(observation, parameters, arm, kernel, physical_command=physical_command, old_logp=old_logp)
    if replay.total_loss.hex() != total.value.hex() or replay.new_logp.hex() != new_logp_node.value.hex() or replay.trace.value.hex() != value_node.value.hex():
        raise ModelError("scalar graph forward differs from stored forward replay")
    if arm == "MAPR":
        base_gradients = backward.parameter_gradients
    else:
        from .optimizer import GradientTensor
        base_gradients = tuple(
            GradientTensor(gradient.name[5:], gradient.shape, gradient.values)
            for gradient in backward.parameter_gradients
            if gradient.name.startswith("base.")
        )
    node_body = [(row.node_id, row.semantic_path, row.primitive, row.parent_node_ids_in_operand_slot_order) for row in backward.node_table]
    return ExactSyntheticStep(
        replay,
        backward.parameter_gradients,
        base_gradients,
        step.clipping.gradients,
        step.parameters,
        step.state,
        hashlib.sha256(json.dumps(node_body, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest(),
        _tensor_digest(backward.parameter_gradients),
        _tensor_digest(step.clipping.gradients),
        hashlib.sha256((_tensor_digest(step.parameters) + _state_digest(step.state)).encode("ascii")).hexdigest(),
    )
