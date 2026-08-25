from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import torch
from torch import Tensor, nn

from .config import MODEL_PARAMETER_COUNT, TOKEN_INDEX
from .rng import orthogonal_gate, xavier_array


class ExactLinear(nn.Module):
    def __init__(self, input_width: int, output_width: int) -> None:
        super().__init__()
        self.input_width = input_width
        self.output_width = output_width
        self.weight = nn.Parameter(torch.empty(output_width, input_width, dtype=torch.float32))
        self.bias = nn.Parameter(torch.zeros(output_width, dtype=torch.float32))

    def initialize(self, bit_generator: np.random.PCG64) -> None:
        values = xavier_array(bit_generator, self.output_width, self.input_width)
        with torch.no_grad():
            self.weight.copy_(torch.from_numpy(values))
            self.bias.zero_()

    def forward(self, value: Tensor) -> Tensor:
        return torch.nn.functional.linear(value, self.weight, self.bias)


class ResetAfterGRU(nn.Module):
    def __init__(self, input_width: int = 5, hidden_width: int = 32) -> None:
        super().__init__()
        self.input_width = input_width
        self.hidden_width = hidden_width
        self.weight_ih = nn.Parameter(torch.empty(3 * hidden_width, input_width, dtype=torch.float32))
        self.weight_hh = nn.Parameter(torch.empty(3 * hidden_width, hidden_width, dtype=torch.float32))
        self.bias_ih = nn.Parameter(torch.zeros(3 * hidden_width, dtype=torch.float32))
        self.bias_hh = nn.Parameter(torch.zeros(3 * hidden_width, dtype=torch.float32))

    def initialize(self, bit_generator: np.random.PCG64) -> None:
        with torch.no_grad():
            for gate in range(3):
                start = gate * self.hidden_width
                stop = start + self.hidden_width
                self.weight_ih[start:stop].copy_(torch.from_numpy(
                    xavier_array(bit_generator, self.hidden_width, self.input_width)
                ))
            for gate in range(3):
                start = gate * self.hidden_width
                stop = start + self.hidden_width
                self.weight_hh[start:stop].copy_(torch.from_numpy(
                    orthogonal_gate(bit_generator, self.hidden_width)
                ))
            self.bias_ih.zero_()
            self.bias_hh.zero_()

    def forward(self, sequence: Tensor) -> Tensor:
        if sequence.ndim != 3 or sequence.shape[-1] != self.input_width:
            raise ValueError("word sequence must have shape [batch,time,5]")
        hidden = torch.zeros(
            sequence.shape[0], self.hidden_width, dtype=torch.float32, device=sequence.device,
        )
        for offset in range(sequence.shape[1]):
            value = sequence[:, offset, :]
            input_gates = torch.nn.functional.linear(value, self.weight_ih, self.bias_ih)
            hidden_gates = torch.nn.functional.linear(hidden, self.weight_hh, self.bias_hh)
            ir, iz, inn = input_gates.chunk(3, dim=-1)
            hr, hz, hn = hidden_gates.chunk(3, dim=-1)
            reset = torch.sigmoid(ir + hr)
            update = torch.sigmoid(iz + hz)
            candidate = torch.tanh(inn + reset * hn)
            hidden = (1.0 - update) * candidate + update * hidden
        return hidden


class SCDMPModel(nn.Module):
    def __init__(self, algorithm_seed: int) -> None:
        super().__init__()
        self.algorithm_seed = int(algorithm_seed)
        self.node_1 = ExactLinear(3, 32)
        self.node_2 = ExactLinear(32, 32)
        self.action_embedding = ExactLinear(3, 8)
        self.word_gru = ResetAfterGRU(5, 32)
        self.f_1 = ExactLinear(73, 64)
        self.f_2 = ExactLinear(64, 64)
        self.f_3 = ExactLinear(64, 2)
        self.gn_1 = ExactLinear(73, 64)
        self.gn_2 = ExactLinear(64, 1)
        self.ge_1 = ExactLinear(113, 64)
        self.ge_2 = ExactLinear(64, 1)
        self._exact_initialize()
        count = sum(parameter.numel() for parameter in self.parameters())
        if count != MODEL_PARAMETER_COUNT:
            raise RuntimeError(f"parameter count {count} != {MODEL_PARAMETER_COUNT}")

    def _exact_initialize(self) -> None:
        bit_generator = np.random.PCG64(710_000 + self.algorithm_seed)
        for layer in (self.node_1, self.node_2, self.action_embedding):
            layer.initialize(bit_generator)
        self.word_gru.initialize(bit_generator)
        for layer in (
            self.f_1, self.f_2, self.f_3, self.gn_1, self.gn_2, self.ge_1, self.ge_2,
        ):
            layer.initialize(bit_generator)

    def node_encoding(self, state: Tensor) -> Tensor:
        return torch.tanh(self.node_2(torch.tanh(self.node_1(state))))

    def action_encoding(self, action_one_hot: Tensor) -> Tensor:
        return torch.tanh(self.action_embedding(action_one_hot))

    def word_encoding(self, word_sequence: Tensor) -> Tensor:
        return self.word_gru(word_sequence)

    def transition_from_encoded(
        self, node: Tensor, action: Tensor, word: Tensor, duration: Tensor,
    ) -> Tensor:
        feature = torch.cat((node, action, word, duration), dim=-1)
        hidden = torch.tanh(self.f_1(feature))
        hidden = torch.tanh(self.f_2(hidden))
        raw = self.f_3(hidden)
        return torch.stack((1.5 * torch.tanh(raw[:, 0]), 0.6 * torch.tanh(raw[:, 1])), dim=-1)

    def node_reward_from_encoded(
        self, node: Tensor, action: Tensor, word: Tensor, duration: Tensor,
    ) -> Tensor:
        feature = torch.cat((node, action, word, duration), dim=-1)
        return self.gn_2(torch.tanh(self.gn_1(feature))).squeeze(-1)

    def edge_reward_from_encoded(
        self, left_node: Tensor, right_node: Tensor, left_action: Tensor,
        right_action: Tensor, word: Tensor, duration: Tensor,
    ) -> Tensor:
        feature = torch.cat(
            (left_node, right_node, left_action, right_action, word, duration), dim=-1,
        )
        return self.ge_2(torch.tanh(self.ge_1(feature))).squeeze(-1)

    def predict_nodes(
        self, normalized_state: Tensor, action_one_hot: Tensor,
        word_sequence: Tensor, duration: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        node = self.node_encoding(normalized_state)
        action = self.action_encoding(action_one_hot)
        encoded_word = self.word_encoding(word_sequence)
        terminal = self.transition_from_encoded(node, action, encoded_word, duration)
        node_reward = self.node_reward_from_encoded(node, action, encoded_word, duration)
        return terminal, node_reward, node, action


def encode_words(words: Sequence[Sequence[str]], device: torch.device | None = None) -> Tensor:
    if not words:
        raise ValueError("cannot encode an empty word batch")
    length = len(words[0])
    if any(len(context_word) != length for context_word in words):
        raise ValueError("word batch must have one duration")
    values = np.zeros((len(words), length, 5), dtype=np.float32)
    for row, context_word in enumerate(words):
        for offset, token in enumerate(context_word, start=1):
            values[row, offset - 1, TOKEN_INDEX[token]] = np.float32(1.0)
            values[row, offset - 1, 4] = np.float32(offset / 12.0)
    return torch.as_tensor(values, dtype=torch.float32, device=device)


def one_hot_actions(actions: np.ndarray, device: torch.device | None = None) -> Tensor:
    indices = np.asarray(actions, dtype=np.int64) + 1
    values = np.eye(3, dtype=np.float32)[indices]
    return torch.as_tensor(values, dtype=torch.float32, device=device)
