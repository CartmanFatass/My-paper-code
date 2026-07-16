"""Core architecture and probability ledger for R49-ORSE-G0.

The four categorical codes in this module are opaque protocol states.  This
module intentionally has no environment, reward, optimizer, checkpoint, or
task-specific dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


EXPERIMENT_ID = "EXP-20260716-r49-orse-g0"
SCHEMA_VERSION = 1
MODEL_SEED = 49041
SYNTHETIC_DATA_SEED = 59041
SAMPLING_SEED = 69041
OPAQUE_CODES = 4
MEMBER_FEATURE_DIM = 12
HIDDEN_DIM = 64
LOW_HIDDEN_PLACEHOLDER_DIM = 64
ACTIVE_SIZES = (1, 2, 3, 4, 6, 8, 12, 16)
CASES_PER_SIZE = 128
PERMUTATIONS_PER_CASE = 8
PADDING_VARIANTS = len(ACTIVE_SIZES) * CASES_PER_SIZE
SAMPLE_REPLAY_SEQUENCES = len(ACTIVE_SIZES) * CASES_PER_SIZE
JOIN_LEAVE_EVENT_PAIRS = 256
MAX_AGE = 500
PARITY_TOLERANCE = 1.0e-6
PREFIX_MIN_NORM = 1.0e-8
PREFIX_MEDIAN_FLOOR = 1.0e-4
PREFIX_SUPPORT_FLOOR = 0.99


@dataclass(frozen=True)
class RosterCase:
    """A padded or unpadded active-roster case.

    ``member_keys`` and ``membership_epochs`` are ledger metadata.  Neither is
    consumed by the network.
    """

    case_id: int
    member_keys: np.ndarray
    observations: np.ndarray
    opaque_codes: np.ndarray
    ages: np.ndarray
    joined: np.ndarray
    processed: np.ndarray
    membership_epochs: np.ndarray
    low_hidden_placeholders: np.ndarray
    active_mask: np.ndarray
    external_order: tuple[int, ...]

    def validate(self) -> None:
        slots = int(len(self.member_keys))
        expected = {
            "observations": (slots, MEMBER_FEATURE_DIM),
            "opaque_codes": (slots,),
            "ages": (slots,),
            "joined": (slots,),
            "processed": (slots,),
            "membership_epochs": (slots,),
            "low_hidden_placeholders": (slots, LOW_HIDDEN_PLACEHOLDER_DIM),
            "active_mask": (slots,),
        }
        for name, shape in expected.items():
            if tuple(np.asarray(getattr(self, name)).shape) != shape:
                raise ValueError(f"{name} shape mismatch: expected {shape}")
        active_indices = np.flatnonzero(self.active_mask)
        active_keys = tuple(int(self.member_keys[index]) for index in active_indices)
        if not active_keys:
            raise ValueError("an R49 case must contain at least one active member")
        if len(set(active_keys)) != len(active_keys):
            raise ValueError("active member keys must be unique")
        if set(active_keys) != set(self.external_order):
            raise ValueError("external AR order must contain each active key once")
        if len(self.external_order) != len(active_keys):
            raise ValueError("external AR order contains duplicate keys")
        active_codes = self.opaque_codes[active_indices]
        if bool(np.any(active_codes < 0)) or bool(np.any(active_codes >= OPAQUE_CODES)):
            raise ValueError("active opaque code is outside the registered support")
        active_ages = self.ages[active_indices]
        if bool(np.any(active_ages < 0)) or bool(np.any(active_ages > MAX_AGE)):
            raise ValueError("active age is outside the registered range")

    @property
    def active_n(self) -> int:
        return int(np.count_nonzero(self.active_mask))

    @property
    def active_keys(self) -> tuple[int, ...]:
        return tuple(int(value) for value in self.member_keys[self.active_mask])


@dataclass(frozen=True)
class AppliedToken:
    member_key: int
    kind: str
    code: int

    def label(self) -> str:
        if self.kind == "KEEP":
            return "KEEP"
        return f"SET:{self.code}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_key": int(self.member_key),
            "kind": str(self.kind),
            "code": int(self.code),
        }


class OpenRosterSetPolicy(nn.Module):
    """N-independent Deep-Sets roster policy used only by the R49 gate."""

    def __init__(
        self,
        member_feature_dim: int = MEMBER_FEATURE_DIM,
        opaque_codes: int = OPAQUE_CODES,
        hidden_dim: int = HIDDEN_DIM,
    ) -> None:
        super().__init__()
        self.member_feature_dim = int(member_feature_dim)
        self.opaque_codes = int(opaque_codes)
        self.hidden_dim = int(hidden_dim)
        member_input_dim = self.member_feature_dim + self.opaque_codes + 3
        roster_input_dim = self.hidden_dim + self.opaque_codes + 2
        decoder_input_dim = self.hidden_dim + (self.hidden_dim + 1) + self.hidden_dim

        self.member_encoder = nn.Sequential(
            nn.Linear(member_input_dim, self.hidden_dim),
            nn.GELU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.roster_encoder = nn.Sequential(
            nn.Linear(roster_input_dim, self.hidden_dim),
            nn.GELU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.decoder_hidden = nn.Linear(decoder_input_dim, self.hidden_dim)
        self.decoder_activation = nn.GELU()
        self.keep_head = nn.Linear(self.hidden_dim, 1)
        self.set_head = nn.Linear(self.hidden_dim, self.opaque_codes)
        self.value_hidden = nn.Linear(self.hidden_dim + 1, self.hidden_dim)
        self.value_activation = nn.GELU()
        self.value_head = nn.Linear(self.hidden_dim, 1)

    @staticmethod
    def normalized_age(ages: torch.Tensor) -> torch.Tensor:
        denominator = float(np.log(501.0))
        return torch.log1p(ages.to(dtype=torch.float32)) / denominator

    def encode_active(
        self,
        case: RosterCase,
    ) -> dict[str, torch.Tensor | tuple[int, ...] | dict[int, int]]:
        case.validate()
        device = next(self.parameters()).device
        active_indices = np.flatnonzero(case.active_mask)
        keys = tuple(int(case.member_keys[index]) for index in active_indices)
        key_to_index = {key: index for index, key in enumerate(keys)}
        observations = torch.as_tensor(
            case.observations[active_indices], dtype=torch.float32, device=device
        )
        codes = torch.as_tensor(
            case.opaque_codes[active_indices], dtype=torch.long, device=device
        )
        ages = torch.as_tensor(
            case.ages[active_indices], dtype=torch.float32, device=device
        )
        joined = torch.as_tensor(
            case.joined[active_indices], dtype=torch.bool, device=device
        )
        processed = torch.as_tensor(
            case.processed[active_indices], dtype=torch.bool, device=device
        )
        member_input = torch.cat(
            (
                observations,
                F.one_hot(codes, num_classes=self.opaque_codes).to(torch.float32),
                self.normalized_age(ages).unsqueeze(-1),
                joined.to(torch.float32).unsqueeze(-1),
                processed.to(torch.float32).unsqueeze(-1),
            ),
            dim=-1,
        )
        member_embeddings = self.member_encoder(member_input)
        log_count = torch.log1p(
            torch.tensor(float(len(keys)), dtype=torch.float32, device=device)
        ).reshape(1)
        team_summary = torch.cat((member_embeddings.mean(dim=0), log_count), dim=0)
        value_features = self.value_activation(self.value_hidden(team_summary))
        value = self.value_head(value_features).squeeze(-1)
        return {
            "keys": keys,
            "key_to_index": key_to_index,
            "member_embeddings": member_embeddings,
            "team_summary": team_summary,
            "value": value,
            "codes": codes,
            "ages": ages,
            "joined": joined,
            "processed": processed,
        }

    def roster_units(
        self,
        member_embeddings: torch.Tensor,
        codes: torch.Tensor,
        ages: torch.Tensor,
        processed: torch.Tensor,
    ) -> torch.Tensor:
        roster_input = torch.cat(
            (
                member_embeddings,
                F.one_hot(codes, num_classes=self.opaque_codes).to(torch.float32),
                self.normalized_age(ages).unsqueeze(-1),
                processed.to(torch.float32).unsqueeze(-1),
            ),
            dim=-1,
        )
        return self.roster_encoder(roster_input)

    def roster_unit(
        self,
        member_embedding: torch.Tensor,
        code: torch.Tensor,
        age: torch.Tensor,
        processed: torch.Tensor,
    ) -> torch.Tensor:
        return self.roster_units(
            member_embedding.unsqueeze(0),
            code.reshape(1),
            age.reshape(1),
            processed.reshape(1),
        ).squeeze(0)

    def decode_pair(
        self,
        member_embedding: torch.Tensor,
        team_summary: torch.Tensor,
        incremental_roster: torch.Tensor,
        full_roster: torch.Tensor,
    ) -> torch.Tensor:
        shared = torch.cat((member_embedding, team_summary), dim=0)
        decoder_input = torch.stack(
            (
                torch.cat((shared, incremental_roster), dim=0),
                torch.cat((shared, full_roster), dim=0),
            ),
            dim=0,
        )
        hidden = self.decoder_activation(self.decoder_hidden(decoder_input))
        keep = self.keep_head(hidden)
        set_codes = self.set_head(hidden)
        return torch.cat((keep, set_codes), dim=-1)


def state_dict_signature(model: nn.Module) -> dict[str, tuple[int, ...]]:
    return {name: tuple(tensor.shape) for name, tensor in model.state_dict().items()}


def parameter_count(model: nn.Module) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters()))


def effective_support_and_log_probs(
    raw_logits: torch.Tensor,
    *,
    current_code: int,
    joined: bool,
    member_key: int,
) -> tuple[list[AppliedToken], torch.Tensor]:
    if tuple(raw_logits.shape) != (1 + OPAQUE_CODES,):
        raise ValueError("R49 decoder logits have the wrong shape")
    keep_logit = raw_logits[0]
    set_logits = raw_logits[1:]
    if joined:
        support = [
            AppliedToken(member_key=int(member_key), kind="SET", code=code)
            for code in range(OPAQUE_CODES)
        ]
        return support, F.log_softmax(set_logits, dim=0)

    set_mask = torch.ones(OPAQUE_CODES, dtype=torch.bool, device=raw_logits.device)
    set_mask[int(current_code)] = False
    allowed_codes = torch.arange(OPAQUE_CODES, device=raw_logits.device)[set_mask]
    conditional_set = F.log_softmax(set_logits[set_mask], dim=0)
    support = [
        AppliedToken(
            member_key=int(member_key), kind="KEEP", code=int(current_code)
        )
    ]
    support.extend(
        AppliedToken(member_key=int(member_key), kind="SET", code=int(code))
        for code in allowed_codes.detach().cpu().tolist()
    )
    log_probs = torch.cat(
        (
            F.logsigmoid(keep_logit).reshape(1),
            F.logsigmoid(-keep_logit).reshape(1) + conditional_set,
        ),
        dim=0,
    )
    return support, log_probs


def support_labels(support: Iterable[AppliedToken]) -> list[str]:
    return [token.label() for token in support]


def _select_teacher_token(
    teacher_token: AppliedToken,
    support: Sequence[AppliedToken],
) -> int:
    labels = support_labels(support)
    try:
        index = labels.index(teacher_token.label())
    except ValueError as error:
        raise ValueError(
            f"teacher token {teacher_token.label()} is outside support {labels}"
        ) from error
    if int(teacher_token.member_key) != int(support[index].member_key):
        raise ValueError("teacher token member key does not match the AR position")
    return int(index)


def _prefix_jacobian_frobenius(
    raw_logits: torch.Tensor,
    roster_input: torch.Tensor,
    *,
    joined: bool,
) -> float:
    outputs = raw_logits[1:] if joined else raw_logits
    squared = torch.zeros((), dtype=roster_input.dtype, device=roster_input.device)
    for index in range(int(outputs.numel())):
        gradient = torch.autograd.grad(
            outputs[index],
            roster_input,
            retain_graph=index + 1 < int(outputs.numel()),
            create_graph=False,
            allow_unused=False,
        )[0]
        squared = squared + torch.sum(gradient * gradient)
    return float(torch.sqrt(squared).detach().cpu())


def run_sequence(
    model: OpenRosterSetPolicy,
    case: RosterCase,
    *,
    teacher_tokens: Sequence[AppliedToken] | None = None,
    sampling_generator: torch.Generator | None = None,
    measure_prefix_gradient: bool = False,
) -> dict[str, Any]:
    """Sample or replay one complete active-only AR sequence."""

    if (teacher_tokens is None) == (sampling_generator is None):
        raise ValueError("provide exactly one of teacher_tokens or sampling_generator")
    case.validate()
    with torch.no_grad():
        encoded = model.encode_active(case)
    keys = tuple(int(value) for value in encoded["keys"])
    key_to_index = dict(encoded["key_to_index"])
    member_embeddings = encoded["member_embeddings"].detach()
    team_summary = encoded["team_summary"].detach()
    value = float(encoded["value"].detach().cpu())
    codes = encoded["codes"].detach().clone()
    ages = encoded["ages"].detach().clone()
    joined = encoded["joined"].detach().clone()
    processed = encoded["processed"].detach().clone()
    active_n = len(keys)
    if teacher_tokens is not None and len(teacher_tokens) != active_n:
        raise ValueError("teacher sequence length must equal active member count")

    with torch.no_grad():
        units = model.roster_units(member_embeddings, codes, ages, processed)
        incremental_roster = units.mean(dim=0)

    sampled_tokens: list[AppliedToken] = []
    token_log_probs: list[float] = []
    token_logits: list[list[float]] = []
    effective_supports: list[list[str]] = []
    applied_prefixes: list[dict[str, Any]] = []
    prefix_gradient_norms: list[float] = []
    incremental_full_logits_max_abs = 0.0
    incremental_full_roster_max_abs = 0.0
    decoder_calls = 0
    incremental_updates = 0

    for position, member_key in enumerate(case.external_order):
        index = int(key_to_index[int(member_key)])
        with torch.no_grad():
            full_units = model.roster_units(member_embeddings, codes, ages, processed)
            full_roster = full_units.mean(dim=0)
        incremental_full_roster_max_abs = max(
            incremental_full_roster_max_abs,
            float(torch.max(torch.abs(incremental_roster - full_roster)).cpu()),
        )

        if measure_prefix_gradient:
            roster_for_gradient = incremental_roster.detach().clone().requires_grad_(True)
            raw_pair = model.decode_pair(
                member_embeddings[index],
                team_summary,
                roster_for_gradient,
                full_roster.detach(),
            )
            gradient_norm = _prefix_jacobian_frobenius(
                raw_pair[0],
                roster_for_gradient,
                joined=bool(joined[index].item()),
            )
            prefix_gradient_norms.append(gradient_norm)
            raw_pair = raw_pair.detach()
        else:
            with torch.no_grad():
                raw_pair = model.decode_pair(
                    member_embeddings[index],
                    team_summary,
                    incremental_roster,
                    full_roster,
                )
        decoder_calls += 1
        incremental_full_logits_max_abs = max(
            incremental_full_logits_max_abs,
            float(torch.max(torch.abs(raw_pair[0] - raw_pair[1])).cpu()),
        )
        raw_logits = raw_pair[0]
        support, log_probs = effective_support_and_log_probs(
            raw_logits,
            current_code=int(codes[index].item()),
            joined=bool(joined[index].item()),
            member_key=int(member_key),
        )
        if teacher_tokens is None:
            probabilities = torch.exp(log_probs)
            selected_index = int(
                torch.multinomial(
                    probabilities,
                    num_samples=1,
                    generator=sampling_generator,
                ).item()
            )
            token = support[selected_index]
        else:
            token = teacher_tokens[position]
            selected_index = _select_teacher_token(token, support)

        token_logits.append(raw_logits.detach().cpu().tolist())
        effective_supports.append(support_labels(support))
        token_log_probs.append(float(log_probs[selected_index].detach().cpu()))
        sampled_tokens.append(token)

        with torch.no_grad():
            old_unit = units[index].clone()
            if token.kind == "SET":
                codes[index] = int(token.code)
                ages[index] = 0.0
            elif token.kind != "KEEP":
                raise ValueError(f"unknown R49 token kind: {token.kind}")
            processed[index] = True
            new_unit = model.roster_unit(
                member_embeddings[index],
                codes[index],
                ages[index],
                processed[index],
            )
            incremental_roster = (
                incremental_roster + (new_unit - old_unit) / float(active_n)
            )
            units = units.clone()
            units[index] = new_unit
        incremental_updates += 1
        applied_prefixes.append(
            {
                "position": int(position),
                "applied_member_key": int(member_key),
                "active_member_keys": [int(value) for value in keys],
                "opaque_codes": [int(value) for value in codes.detach().cpu().tolist()],
                "ages": [float(value) for value in ages.detach().cpu().tolist()],
                "processed": [bool(value) for value in processed.detach().cpu().tolist()],
            }
        )

    with torch.no_grad():
        final_full = model.roster_units(member_embeddings, codes, ages, processed).mean(
            dim=0
        )
    incremental_full_roster_max_abs = max(
        incremental_full_roster_max_abs,
        float(torch.max(torch.abs(incremental_roster - final_full)).cpu()),
    )
    return {
        "value": value,
        "tokens": sampled_tokens,
        "token_log_probs": token_log_probs,
        "token_logits": token_logits,
        "effective_supports": effective_supports,
        "applied_prefixes": applied_prefixes,
        "prefix_gradient_norms": prefix_gradient_norms,
        "incremental_full_logits_max_abs": float(
            incremental_full_logits_max_abs
        ),
        "incremental_full_roster_max_abs": float(
            incremental_full_roster_max_abs
        ),
        "complexity": {
            "active_set_full_encode_calls": 1,
            "incremental_updates": int(incremental_updates),
            "decoder_calls": int(decoder_calls),
            "pairwise_n_by_n_tensor_count": 0,
        },
    }


def parameter_gradient_audit(
    model: OpenRosterSetPolicy,
    case: RosterCase,
) -> dict[str, Any]:
    """Audit finite gradients without populating ``.grad`` or taking a step."""

    encoded = model.encode_active(case)
    embeddings = encoded["member_embeddings"]
    summary = encoded["team_summary"]
    codes = encoded["codes"]
    ages = encoded["ages"]
    processed = encoded["processed"]
    roster = model.roster_units(embeddings, codes, ages, processed).mean(dim=0)
    raw_pair = model.decode_pair(embeddings[0], summary, roster, roster)
    scalar = raw_pair.sum() + encoded["value"]
    parameters = tuple(model.parameters())
    gradients = torch.autograd.grad(
        scalar,
        parameters,
        retain_graph=False,
        create_graph=False,
        allow_unused=True,
    )
    finite = True
    unused: list[str] = []
    norms: dict[str, float] = {}
    for (name, _parameter), gradient in zip(model.named_parameters(), gradients):
        if gradient is None:
            unused.append(name)
            finite = False
            continue
        finite = finite and bool(torch.all(torch.isfinite(gradient)).item())
        norms[name] = float(torch.linalg.vector_norm(gradient).detach().cpu())
    return {
        "all_finite": bool(finite),
        "unused_parameters": unused,
        "gradient_norms": norms,
    }


def max_abs_nested(left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]) -> float:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if left_array.shape != right_array.shape:
        return float("inf")
    if not left_array.size:
        return 0.0
    return float(np.max(np.abs(left_array - right_array)))


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return json_ready(value.detach().cpu().numpy())
    if isinstance(value, AppliedToken):
        return value.to_dict()
    return value
