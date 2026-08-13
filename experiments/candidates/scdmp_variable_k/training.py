from __future__ import annotations

import copy
from collections.abc import Callable, Sequence

import numpy as np
import torch
from torch import Tensor

from .config import ADAM, COMPOSITION_WEIGHT, N_AGENTS, OPTIMIZER_UPDATES
from .corpus import BankRow, Corpus, LockedBatch, LockedBatchStream, Scales, support_certificate
from .lifecycle import Lifecycle
from .model import SCDMPModel, encode_words, one_hot_actions


ResourceCheck = Callable[[], None]


def model_call_batch(
    model: SCDMPModel,
    state_e: np.ndarray | Tensor,
    state_v: np.ndarray | Tensor,
    state_q: np.ndarray | Tensor,
    actions: np.ndarray,
    words: Sequence[tuple[str, ...]],
    before_forward: Callable[[], None] | None = None,
) -> tuple[Tensor, Tensor, Tensor]:
    """Evaluate complete four-agent rows in one semantics-preserving batch."""
    e = state_e if isinstance(state_e, Tensor) else torch.as_tensor(state_e, dtype=torch.float32)
    v = state_v if isinstance(state_v, Tensor) else torch.as_tensor(state_v, dtype=torch.float32)
    q = state_q if isinstance(state_q, Tensor) else torch.as_tensor(state_q, dtype=torch.float32)
    q = q.to(device=e.device, dtype=torch.float32)
    if e.ndim != 2 or e.shape[1] != N_AGENTS or v.shape != e.shape or q.shape != e.shape:
        raise ValueError("batched states must have shape [rows,4]")
    row_count = e.shape[0]
    if len(words) != row_count or any(len(item) != len(words[0]) for item in words):
        raise ValueError("one equal-duration word is required per complete row")
    normalized = torch.stack((e / 1.5, v / 0.6, q), dim=-1).to(dtype=torch.float32)
    action_tensor = one_hot_actions(np.asarray(actions, dtype=np.int64), device=e.device)
    word_tensor = encode_words(
        [context_word for context_word in words for _slot in range(N_AGENTS)], device=e.device,
    ).reshape(row_count, N_AGENTS, len(words[0]), 5)
    duration = torch.full(
        (row_count, N_AGENTS, 1), len(words[0]) / 12.0,
        dtype=torch.float32, device=e.device,
    )
    flat_state = normalized.reshape(-1, 3)
    flat_action = action_tensor.reshape(-1, 3)
    flat_word = word_tensor.reshape(-1, len(words[0]), 5)
    flat_duration = duration.reshape(-1, 1)
    if before_forward is not None:
        before_forward()
    node_encoding = model.node_encoding(flat_state)
    action_encoding = model.action_encoding(flat_action)
    encoded_word_flat = model.word_encoding(flat_word)
    terminal = model.transition_from_encoded(
        node_encoding, action_encoding, encoded_word_flat, flat_duration,
    )
    node_reward = model.node_reward_from_encoded(
        node_encoding, action_encoding, encoded_word_flat, flat_duration,
    )
    terminal = terminal.reshape(row_count, N_AGENTS, 2)
    node_reward = node_reward.reshape(row_count, N_AGENTS)
    node_encoding = node_encoding.reshape(row_count, N_AGENTS, -1)
    action_encoding = action_encoding.reshape(row_count, N_AGENTS, -1)
    encoded_word = encoded_word_flat.reshape(row_count, N_AGENTS, -1)
    right_node = torch.roll(node_encoding, shifts=-1, dims=1)
    right_action = torch.roll(action_encoding, shifts=-1, dims=1)
    edge_reward = model.edge_reward_from_encoded(
        node_encoding.reshape(-1, 32), right_node.reshape(-1, 32),
        action_encoding.reshape(-1, 8), right_action.reshape(-1, 8),
        encoded_word.reshape(-1, 32), duration.reshape(-1, 1),
    ).reshape(row_count, N_AGENTS)
    return terminal, node_reward, edge_reward


def _arrays(rows: Sequence[BankRow]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[str, ...]]]:
    return (
        np.stack([row.initial.e for row in rows]),
        np.stack([row.initial.v for row in rows]),
        np.stack([row.initial.q for row in rows]),
        [row.word for row in rows],
    )


def _endpoint_bank_loss(
    model: SCDMPModel, rows: Sequence[BankRow], scales: Scales,
    before_forward: Callable[[], None] | None = None,
) -> Tensor:
    initial_e, initial_v, initial_q, words = _arrays(rows)
    actions = np.asarray([row.action for row in rows], dtype=np.int64)
    terminal, node_reward, edge_reward = model_call_batch(
        model, initial_e, initial_v, initial_q, actions, words,
        before_forward=before_forward,
    )
    target_terminal = torch.as_tensor(
        np.stack([np.stack((row.terminal.e, row.terminal.v), axis=-1) for row in rows]),
        dtype=torch.float32,
    )
    node_target = torch.as_tensor(np.stack([row.node_rewards for row in rows]), dtype=torch.float32)
    edge_target = torch.as_tensor(np.stack([row.edge_rewards for row in rows]), dtype=torch.float32)
    coordinate_scale = torch.tensor((scales.e, scales.v), dtype=torch.float32)
    row_loss = (
        torch.square((terminal - target_terminal) / coordinate_scale).mean(dim=(1, 2))
        + torch.square((node_reward - node_target) / scales.node_reward).mean(dim=1)
        + torch.square((edge_reward - edge_target) / scales.edge_reward).mean(dim=1)
    )
    return row_loss.mean()


def _composition_bank_loss(model: SCDMPModel, rows: Sequence[BankRow], scales: Scales) -> Tensor:
    split = int(rows[0].split or 0)
    if split <= 0 or any(row.split != split for row in rows):
        raise ValueError("composition batch must have one positive split")
    initial_e, initial_v, initial_q, words = _arrays(rows)
    actions = np.asarray([row.action for row in rows], dtype=np.int64)
    prefixes = [item[:split] for item in words]
    suffixes = [item[split:] for item in words]
    direct_terminal, direct_node, direct_edge = model_call_batch(
        model, initial_e, initial_v, initial_q, actions, words,
    )
    prefix_terminal, prefix_node, prefix_edge = model_call_batch(
        model, initial_e, initial_v, initial_q, actions, prefixes,
    )
    suffix_terminal, suffix_node, suffix_edge = model_call_batch(
        model, prefix_terminal[:, :, 0], prefix_terminal[:, :, 1], initial_q,
        actions, suffixes,
    )
    coordinate_scale = torch.tensor((scales.e, scales.v), dtype=torch.float32)
    row_loss = (
        torch.square((direct_terminal - suffix_terminal) / coordinate_scale).mean(dim=(1, 2))
        + torch.square((direct_node - prefix_node - suffix_node) / scales.node_reward).mean(dim=1)
        + torch.square((direct_edge - prefix_edge - suffix_edge) / scales.edge_reward).mean(dim=1)
    )
    return row_loss.mean()


def losses(
    model: SCDMPModel, batch: LockedBatch, scales: Scales,
    before_first_forward: Callable[[], None] | None = None,
) -> tuple[Tensor, Tensor]:
    endpoint_losses = []
    for bank_index, bank in enumerate(("E_2", "E_4", "E_8")):
        endpoint_losses.append(_endpoint_bank_loss(
            model, batch.rows[bank], scales,
            before_forward=before_first_forward if bank_index == 0 else None,
        ))
    endpoint = torch.stack(endpoint_losses).mean()
    composition = torch.stack([
        _composition_bank_loss(model, batch.rows[bank], scales) for bank in ("C_22", "C_44")
    ]).mean()
    return endpoint, composition


def _optimizer(model: SCDMPModel) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.parameters(), lr=ADAM["lr"], betas=ADAM["betas"],
        eps=ADAM["eps"], weight_decay=ADAM["weight_decay"],
    )


def train_paired(
    corpus: Corpus,
    algorithm_seed: int,
    lifecycle: Lifecycle,
    resource_check: ResourceCheck | None = None,
) -> tuple[dict[str, SCDMPModel], dict[str, object]]:
    scdmp = SCDMPModel(algorithm_seed)
    models = {"SCDMP": scdmp, "SCDMP-NOCOMP": copy.deepcopy(scdmp)}
    left_state = models["SCDMP"].state_dict()
    right_state = models["SCDMP-NOCOMP"].state_dict()
    if any(not torch.equal(left_state[name], right_state[name]) for name in left_state):
        raise RuntimeError("paired initial tensors are not byte-identical")
    optimizers = {arm: _optimizer(model) for arm, model in models.items()}
    stream = LockedBatchStream(corpus, algorithm_seed)
    locked_zero = stream.next_batch()
    certificate = support_certificate(corpus, locked_zero)
    with torch.no_grad():
        _, initial_composition = losses(models["SCDMP"], locked_zero, corpus.scales)
        d_comp_init = float(torch.sqrt(initial_composition).item())
    final_losses: dict[str, float] = {}
    for update_index in range(OPTIMIZER_UPDATES):
        if resource_check is not None:
            resource_check()
        batch = locked_zero if update_index == 0 else stream.next_batch()
        for arm in ("SCDMP", "SCDMP-NOCOMP"):
            optimizer = optimizers[arm]
            optimizer.zero_grad(set_to_none=True)
            activity_callback = None
            if update_index == 0 and arm == "SCDMP":
                activity_callback = lambda: lifecycle.begin_update_zero(
                    support_certificate=certificate,
                )
            endpoint_loss, composition_loss = losses(
                models[arm], batch, corpus.scales,
                before_first_forward=activity_callback,
            )
            total = endpoint_loss + COMPOSITION_WEIGHT[arm] * composition_loss
            total.backward()
            torch.nn.utils.clip_grad_norm_(models[arm].parameters(), ADAM["gradient_norm_clip"])
            optimizer.step()
            final_losses[arm] = float(total.detach().item())
    return models, {
        "support_certificate": certificate,
        "D_comp_init": d_comp_init,
        "updates_per_arm": OPTIMIZER_UPDATES,
        "arm_order": ["SCDMP", "SCDMP-NOCOMP"],
        "final_losses": final_losses,
        "checkpoint_rule": "final_update_only",
        "batched_complete_rows": True,
    }


def train_support_probe(model: SCDMPModel, corpus: Corpus) -> dict[str, object]:
    """Untouched support error with the endpoint objective's equal-duration weighting."""
    per_duration: dict[str, dict[str, float]] = {}
    component_bank_mse: dict[str, list[float]] = {"F": [], "node": [], "edge": []}
    with torch.no_grad():
        for duration in (2, 4, 8):
            rows = corpus.probe_rows[duration]
            initial_e, initial_v, initial_q, words = _arrays(rows)
            actions = np.asarray([row.action for row in rows], dtype=np.int64)
            terminal, node, edge = model_call_batch(
                model, initial_e, initial_v, initial_q, actions, words,
            )
            true_terminal = torch.as_tensor(
                np.stack([np.stack((row.terminal.e, row.terminal.v), axis=-1) for row in rows]),
                dtype=torch.float32,
            )
            true_node = torch.as_tensor(np.stack([row.node_rewards for row in rows]), dtype=torch.float32)
            true_edge = torch.as_tensor(np.stack([row.edge_rewards for row in rows]), dtype=torch.float32)
            scale = torch.tensor((corpus.scales.e, corpus.scales.v), dtype=torch.float32)
            mse = {
                "F": float(torch.square((terminal - true_terminal) / scale).mean().item()),
                "node": float(torch.square((node - true_node) / corpus.scales.node_reward).mean().item()),
                "edge": float(torch.square((edge - true_edge) / corpus.scales.edge_reward).mean().item()),
            }
            for name, value in mse.items():
                component_bank_mse[name].append(value)
            rms = {name: float(np.sqrt(value)) for name, value in mse.items()}
            per_duration[str(duration)] = {**rms, "composite": float(np.mean(list(rms.values())))}
    component_rmse = {
        name: float(np.sqrt(np.mean(values))) for name, values in component_bank_mse.items()
    }
    return {
        "rows_per_duration": {str(k): len(corpus.probe_rows[k]) for k in (2, 4, 8)},
        "per_duration": per_duration,
        "equal_duration_component_rmse": component_rmse,
        "composite_standardized_rmse": float(np.mean(list(component_rmse.values()))),
        "reduction": "mean of F/node/edge RMSE; each component averages banks k=2,4,8 equally",
    }
