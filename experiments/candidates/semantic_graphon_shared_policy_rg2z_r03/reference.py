"""Small deterministic formulas for independent implementation conformance."""

from __future__ import annotations

import math
from typing import Sequence

import torch

from .config import (
    BASE_P0,
    KERNEL_EPSILON,
    LATENCY,
    LOAD_LOGIT_SLOPE,
    P0,
    ROTATED_PHYSICAL_COLUMN_SOURCE,
)


def logistic(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def loaded_probability(p0: float, sender_count: int) -> float:
    return logistic(math.log(p0 / (1.0 - p0)) - LOAD_LOGIT_SLOPE * (sender_count - 1))


def uplink_probability(receiver_role: int, sender_role: int, sender_count: int) -> float:
    return loaded_probability(P0[receiver_role][sender_role], sender_count)


def base_probability(relay_count: int) -> float:
    return loaded_probability(BASE_P0, relay_count)


def physical_kernel(
    receiver_role: int,
    sender_role: int,
    sender_count: int,
    *,
    rotated: bool = False,
) -> float:
    physical_sender = (
        ROTATED_PHYSICAL_COLUMN_SOURCE[sender_role] if rotated else sender_role
    )
    return (
        loaded_probability(P0[receiver_role][physical_sender], sender_count)
        / LATENCY[receiver_role][physical_sender]
    )


def load_coordinate(sender_count: int) -> float:
    return (2.0 * math.log(sender_count) - math.log(14.0)) / math.log(7.0 / 2.0)


def reference_role_summary(
    role_message_sums: Sequence[Sequence[float]],
    counts: Sequence[int],
    beta: Sequence[Sequence[Sequence[float]]],
    receiver_role: int,
    *,
    rotated: bool = False,
) -> tuple[list[float], float]:
    if len(role_message_sums) != 3 or len(counts) != 3:
        raise ValueError("exactly three public roles are required")
    width = len(role_message_sums[0])
    numerator = [0.0] * width
    denominator = 0.0
    for sender_role in range(3):
        count = counts[sender_role]
        residual = (
            beta[receiver_role][sender_role][0]
            + beta[receiver_role][sender_role][1] * load_coordinate(count)
        )
        omega = physical_kernel(
            receiver_role, sender_role, count, rotated=rotated
        ) * math.exp(residual)
        denominator += count * omega
        for index in range(width):
            numerator[index] += omega * role_message_sums[sender_role][index]
    return [value / (denominator + KERNEL_EPSILON) for value in numerator], denominator


def reset_before_matrix_gru(
    actor_input: torch.Tensor,
    previous_hidden: torch.Tensor,
    W_z: torch.Tensor,
    W_r: torch.Tensor,
    W_n: torch.Tensor,
    U_z: torch.Tensor,
    U_r: torch.Tensor,
    U_n: torch.Tensor,
    b_z: torch.Tensor,
    b_r: torch.Tensor,
    b_n: torch.Tensor,
) -> torch.Tensor:
    z = torch.sigmoid(actor_input @ W_z.T + previous_hidden @ U_z.T + b_z)
    r = torch.sigmoid(actor_input @ W_r.T + previous_hidden @ U_r.T + b_r)
    candidate = torch.tanh(actor_input @ W_n.T + (r * previous_hidden) @ U_n.T + b_n)
    return (1.0 - z) * candidate + z * previous_hidden


def episode_return(west_deliveries: int, east_deliveries: int, waste: float) -> float:
    if not (0 <= west_deliveries <= 3 and 0 <= east_deliveries <= 3):
        raise ValueError("each basin has exactly three distinct events")
    if not 0.0 <= waste <= 1.0:
        raise ValueError("waste must be a fraction")
    return (
        0.65 * (west_deliveries + east_deliveries) / 6.0
        + 0.25 * min(west_deliveries, east_deliveries) / 3.0
        + 0.10 * (1.0 - waste)
    )


def overflow_before_ack_fixture() -> dict[str, tuple[str, ...]]:
    """Deterministic certificate fixture for literal arrival-then-current-head ACK."""
    before = ["transmitted", "second", "third", "fourth"]
    after_arrival = [*before, "arrival"]
    after_arrival.pop(0)  # capacity-four overflow drops the old head
    before_ack = tuple(after_arrival)
    after_arrival.pop(0)  # step 2 removes the current head, not an object match
    after_ack = tuple(after_arrival)
    expected_before_ack = ("second", "third", "fourth", "arrival")
    expected_after_ack = ("third", "fourth", "arrival")
    if before_ack != expected_before_ack or after_ack != expected_after_ack:
        raise AssertionError("arrival/overflow/ack reference ordering drifted")
    return {
        "initial": tuple(before),
        "after_arrival_before_ack": before_ack,
        "after_current_head_ack": after_ack,
    }
