from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
import torch
from torch import Tensor

from ..corpus import BankRow
from ..model import encode_words, one_hot_actions
from .config import N_AGENTS
from .corpus import LockedBatch, Scales
from .model import SCDMPModel


def model_call_batch(model: SCDMPModel, state_e: np.ndarray | Tensor,
    state_v: np.ndarray | Tensor, state_q: np.ndarray | Tensor, actions: np.ndarray,
    words: Sequence[tuple[str, ...]]) -> tuple[Tensor, Tensor, Tensor]:
    e = state_e if isinstance(state_e, Tensor) else torch.as_tensor(state_e, dtype=torch.float32)
    v = state_v if isinstance(state_v, Tensor) else torch.as_tensor(state_v, dtype=torch.float32)
    q = state_q if isinstance(state_q, Tensor) else torch.as_tensor(state_q, dtype=torch.float32)
    q = q.to(device=e.device, dtype=torch.float32)
    if e.ndim != 2 or e.shape[1] != N_AGENTS or v.shape != e.shape or q.shape != e.shape:
        raise ValueError("complete rows require [rows,4] states")
    if len(words) != e.shape[0] or not words or any(len(w) != len(words[0]) for w in words):
        raise ValueError("one equal-duration word per row required")
    normalized = torch.stack((e / 1.5, v / 0.6, q), dim=-1).to(torch.float32)
    action = one_hot_actions(np.asarray(actions, dtype=np.int64), device=e.device)
    word = encode_words([w for w in words for _ in range(N_AGENTS)], device=e.device).reshape(
        e.shape[0], N_AGENTS, len(words[0]), 5)
    duration = torch.full((e.shape[0], N_AGENTS, 1), len(words[0]) / 12.0,
        dtype=torch.float32, device=e.device)
    flat_state = normalized.reshape(-1, 3)
    flat_action = action.reshape(-1, 3)
    flat_word = word.reshape(-1, len(words[0]), 5)
    flat_duration = duration.reshape(-1, 1)
    node_enc = model.node_encoding(flat_state)
    action_enc = model.action_encoding(flat_action)
    word_enc = model.word_encoding(flat_word)
    terminal = model.transition_from_encoded(node_enc, action_enc, word_enc, flat_duration)
    node = model.node_reward_from_encoded(node_enc, action_enc, word_enc, flat_duration)
    node_rows = node_enc.reshape(e.shape[0], N_AGENTS, -1)
    action_rows = action_enc.reshape(e.shape[0], N_AGENTS, -1)
    word_rows = word_enc.reshape(e.shape[0], N_AGENTS, -1)
    edge = model.edge_reward_from_encoded(node_rows.reshape(-1, 32),
        torch.roll(node_rows, -1, 1).reshape(-1, 32), action_rows.reshape(-1, 8),
        torch.roll(action_rows, -1, 1).reshape(-1, 8), word_rows.reshape(-1, 32),
        duration.reshape(-1, 1))
    return terminal.reshape(-1, N_AGENTS, 2), node.reshape(-1, N_AGENTS), edge.reshape(-1, N_AGENTS)


def arrays(rows: Sequence[BankRow]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[tuple[str, ...]]]:
    return (np.stack([r.initial.e for r in rows]), np.stack([r.initial.v for r in rows]),
            np.stack([r.initial.q for r in rows]), np.asarray([r.action for r in rows], dtype=np.int64),
            [r.word for r in rows])


def standardized_row_loss(pred: tuple[Tensor, Tensor, Tensor], terminal: np.ndarray,
    node: np.ndarray, edge: np.ndarray, scales: Scales) -> Tensor:
    target_f = torch.as_tensor(terminal, dtype=torch.float32)
    target_n = torch.as_tensor(node, dtype=torch.float32)
    target_e = torch.as_tensor(edge, dtype=torch.float32)
    fscale = torch.tensor((scales.e, scales.v), dtype=torch.float32)
    return (torch.square((pred[0] - target_f) / fscale).mean((1, 2))
            + torch.square((pred[1] - target_n) / scales.node_reward).mean(1)
            + torch.square((pred[2] - target_e) / scales.edge_reward).mean(1))


def endpoint_loss(model: SCDMPModel, batch: LockedBatch, scales: Scales) -> Tensor:
    losses = []
    for bank in ("E_2", "E_4", "E_8"):
        rows = batch.rows[bank]
        e, v, q, actions, words = arrays(rows)
        pred = model_call_batch(model, e, v, q, actions, words)
        true_f = np.stack([np.stack((r.terminal.e, r.terminal.v), -1) for r in rows])
        losses.append(standardized_row_loss(pred, true_f,
            np.stack([r.node_rewards for r in rows]), np.stack([r.edge_rewards for r in rows]), scales).mean())
    return torch.stack(losses).mean()


def _relation_bank_loss(model: SCDMPModel, rows: Sequence[BankRow], scales: Scales, arm: str) -> Tensor:
    split = int(rows[0].split or 0)
    if split <= 0 or any(r.split != split for r in rows):
        raise ValueError("one positive split per auxiliary batch")
    e, v, q, actions, words = arrays(rows)
    p = [w[:split] for w in words]
    suffix = [w[split:] for w in words]
    direct = model_call_batch(model, e, v, q, actions, words)
    if arm == "FREE-DIRECT":
        first = model_call_batch(model, e, v, q, actions, p)
        yp_e = np.stack([r.intermediate.e for r in rows])
        yp_v = np.stack([r.intermediate.v for r in rows])
        second = model_call_batch(model, yp_e, yp_v, q, actions, suffix)
        true_w = np.stack([np.stack((r.terminal.e, r.terminal.v), -1) for r in rows])
        true_p = np.stack([np.stack((r.intermediate.e, r.intermediate.v), -1) for r in rows])
        loss_w = standardized_row_loss(direct, true_w, np.stack([r.node_rewards for r in rows]),
            np.stack([r.edge_rewards for r in rows]), scales)
        loss_p = standardized_row_loss(first, true_p, np.stack([r.prefix_node_rewards for r in rows]),
            np.stack([r.prefix_edge_rewards for r in rows]), scales)
        loss_q = standardized_row_loss(second, true_w, np.stack([r.suffix_node_rewards for r in rows]),
            np.stack([r.suffix_edge_rewards for r in rows]), scales)
        return ((loss_w + loss_p + loss_q) / 3.0).mean()
    first_words, outer_words = (p, suffix) if arm == "SCDMP-CORRECT" else (suffix, p)
    first = model_call_batch(model, e, v, q, actions, first_words)
    outer = model_call_batch(model, first[0][:, :, 0], first[0][:, :, 1], q, actions, outer_words)
    fscale = torch.tensor((scales.e, scales.v), dtype=torch.float32)
    row = (torch.square((direct[0] - outer[0]) / fscale).mean((1, 2))
           + torch.square((direct[1] - first[1] - outer[1]) / scales.node_reward).mean(1)
           + torch.square((direct[2] - first[2] - outer[2]) / scales.edge_reward).mean(1))
    return row.mean()


def auxiliary_loss(model: SCDMPModel, batch: LockedBatch, scales: Scales, arm: str) -> Tensor:
    if arm not in ("FREE-DIRECT", "SCDMP-CORRECT", "SCDMP-ORDER-SHUFFLE"):
        raise ValueError(arm)
    return torch.stack([_relation_bank_loss(model, batch.rows[b], scales, arm)
                        for b in ("C_22", "C_44")]).mean()


def relation_call_spec(row: BankRow, arm: str) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    split = int(row.split or 0)
    p, q = row.word[:split], row.word[split:]
    recursive = (p, q) if arm == "SCDMP-CORRECT" else (q, p)
    return (("direct", row.word, "true_start"), ("first", recursive[0], "true_start"),
            ("outer", recursive[1], "predicted_first"))


def homogeneous_relation_certificate(rows: Sequence[BankRow]) -> dict[str, object]:
    homogeneous = [r for r in rows if len(set(r.word)) == 1]
    words_identical = all(r.word[:int(r.split or 0)] == r.word[int(r.split or 0):] for r in homogeneous)
    specs_identical = all(relation_call_spec(r, "SCDMP-CORRECT") ==
                          relation_call_spec(r, "SCDMP-ORDER-SHUFFLE") for r in homogeneous)
    return {"rows": len(homogeneous), "p_q_byte_identical": words_identical,
            "serialized_call_specs_identical": specs_identical,
            "conforming": bool(homogeneous and words_identical and specs_identical)}

