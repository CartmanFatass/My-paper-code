"""Float64 learned fusions and the one shared actor for revision 06.

The covariance model's Latin loading is literally ``u_i := softplus(b_i)``.
No evidence value, count, multiplicity, time, reward, action, future value, or
held-out statistic is an input to that network.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, pi, sqrt
from typing import Iterable

import numpy as np

from .config import EPSILON_SUPPORT, MU, Phase, STREAMS
from .rng import uniform


def sigmoid(x: np.ndarray) -> np.ndarray:
    positive = x >= 0
    out = np.empty_like(x, dtype=np.float64)
    out[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    out[~positive] = exp_x / (1.0 + exp_x)
    return out


def softplus(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0) + np.log1p(np.exp(-np.abs(x)))


def silu(x: np.ndarray) -> np.ndarray:
    return x * sigmoid(x)


def _silu_grad(x: np.ndarray) -> np.ndarray:
    s = sigmoid(x)
    return s * (1.0 + x * (1.0 - s))


@dataclass
class Adam:
    parameters: list[np.ndarray]
    learning_rate: float
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8

    def __post_init__(self) -> None:
        self.m = [np.zeros_like(p, dtype=np.float64) for p in self.parameters]
        self.v = [np.zeros_like(p, dtype=np.float64) for p in self.parameters]
        self.step_index = 0

    def step(self, gradients: list[np.ndarray]) -> None:
        self.step_index += 1
        correction1 = 1.0 - self.beta1**self.step_index
        correction2 = 1.0 - self.beta2**self.step_index
        for parameter, gradient, first, second in zip(self.parameters, gradients, self.m, self.v):
            first *= self.beta1
            first += (1.0 - self.beta1) * gradient
            second *= self.beta2
            second += (1.0 - self.beta2) * gradient * gradient
            parameter -= self.learning_rate * (first / correction1) / (np.sqrt(second / correction2) + self.epsilon)


class MLP:
    def __init__(self, widths: tuple[int, ...], seed: int, module_id: int, parameter_index_offset: int = 0) -> None:
        self.widths = widths
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        parameter_index = parameter_index_offset
        for fan_in, fan_out in zip(widths[:-1], widths[1:]):
            bound = sqrt(6.0 / (fan_in + fan_out))
            weight = np.empty((fan_in, fan_out), dtype=np.float64)
            for flat_index in range(weight.size):
                draw = uniform(seed, Phase.TRAIN_OPT, STREAMS["TRAIN_OPT_INIT"], module_id, parameter_index)
                weight.flat[flat_index] = -bound + 2.0 * bound * draw
                parameter_index += 1
            bias = np.zeros(fan_out, dtype=np.float64)
            parameter_index += fan_out
            self.weights.append(weight)
            self.biases.append(bias)

    @property
    def parameters(self) -> list[np.ndarray]:
        result: list[np.ndarray] = []
        for weight, bias in zip(self.weights, self.biases):
            result.extend((weight, bias))
        return result

    @property
    def parameter_count(self) -> int:
        return sum(parameter.size for parameter in self.parameters)

    def forward(self, x: np.ndarray, cache: bool = False):
        value = np.asarray(x, dtype=np.float64)
        activations = [value]
        preactivations: list[np.ndarray] = []
        for index, (weight, bias) in enumerate(zip(self.weights, self.biases)):
            pre = value @ weight + bias
            preactivations.append(pre)
            value = silu(pre) if index < len(self.weights) - 1 else pre
            activations.append(value)
        return (value, (activations, preactivations)) if cache else value

    def forward_row_streaming(self, row: np.ndarray) -> np.ndarray:
        """Cache-free, ascending-index float64 inference for one row."""
        value = np.asarray(row, dtype=np.float64)
        for layer_index, (weight, bias) in enumerate(zip(self.weights, self.biases)):
            output = np.empty(weight.shape[1], dtype=np.float64)
            for output_index in range(weight.shape[1]):
                accumulator = np.float64(bias[output_index])
                for input_index in range(weight.shape[0]):
                    accumulator = np.float64(accumulator + value[input_index] * weight[input_index, output_index])
                output[output_index] = accumulator
            value = silu(output) if layer_index < len(self.weights) - 1 else output
        return value

    def backward(self, output_gradient: np.ndarray, cache) -> tuple[np.ndarray, list[np.ndarray]]:
        activations, preactivations = cache
        gradient = np.asarray(output_gradient, dtype=np.float64)
        reversed_gradients: list[tuple[np.ndarray, np.ndarray]] = []
        for layer in range(len(self.weights) - 1, -1, -1):
            if layer < len(self.weights) - 1:
                gradient = gradient * _silu_grad(preactivations[layer])
            input_value = activations[layer]
            weight_gradient = input_value.T @ gradient
            bias_gradient = np.sum(gradient, axis=0)
            gradient = gradient @ self.weights[layer].T
            reversed_gradients.append((weight_gradient, bias_gradient))
        gradients: list[np.ndarray] = []
        for weight_gradient, bias_gradient in reversed(reversed_gradients):
            gradients.extend((weight_gradient, bias_gradient))
        return gradient, gradients

    def state(self) -> dict:
        return {"widths": self.widths, "parameters": [value.tolist() for value in self.parameters]}


def _sum_gradients(accumulator: list[np.ndarray], gradients: list[np.ndarray]) -> None:
    for destination, source in zip(accumulator, gradients):
        destination += source


def _zeros_like(parameters: Iterable[np.ndarray]) -> list[np.ndarray]:
    return [np.zeros_like(parameter) for parameter in parameters]


class CCICModel:
    """The exact 2->16->2 covariance network (82 trainable scalars)."""

    forbidden_inputs = (
        "z",
        "received_count",
        "unique_count",
        "duplicate_multiplicity",
        "t",
        "k",
        "reward",
        "action",
        "future",
        "evaluation_statistics",
        "actor_output",
    )
    allowed_inputs = ("overlap_code", "quality")

    def __init__(self, seed: int) -> None:
        self.network = MLP((2, 16, 2), seed, 0)
        if self.network.parameter_count != 82:
            raise AssertionError("CCIC parameter count changed")
        self.optimizer = Adam(self.network.parameters, learning_rate=3e-3)

    def row_parameters(self, overlap: np.ndarray, quality: np.ndarray, cache: bool = False):
        metadata = np.column_stack((overlap, quality)).astype(np.float64, copy=False)
        if cache:
            raw, network_cache = self.network.forward(metadata, cache=True)
        else:
            raw = np.empty((metadata.shape[0], 2), dtype=np.float64)
            for row_index in range(metadata.shape[0]):
                raw[row_index] = self.network.forward_row_streaming(metadata[row_index])
            network_cache = None
        a = raw[:, 0]
        b = raw[:, 1]
        d = 1e-4 + softplus(a)
        u = softplus(b)  # literal Latin-u assignment required by revision 06
        if not np.all(np.isfinite(d)) or not np.all(np.isfinite(u)) or np.any(d <= 0.0):
            raise FloatingPointError("invalid CCIC covariance parameters")
        if not cache:
            self.last_streaming_trace = {
                "unique_rows": int(metadata.shape[0]),
                "row_order": "ascending",
                "cache_free": True,
                "functional_stages": ("2->16 linear", "SiLU", "16->2 linear", "softplus d/u", "Woodbury sums"),
            }
        return (d, u, (raw, network_cache)) if cache else (d, u)

    def covariance(self, overlap: np.ndarray, quality: np.ndarray) -> np.ndarray:
        d, u = self.row_parameters(overlap, quality)
        return np.diag(d) + np.outer(u, u)

    def fusion(self, z: np.ndarray, overlap: np.ndarray, quality: np.ndarray) -> tuple[float, float]:
        if z.size == 0:
            self.last_streaming_trace = {
                "unique_rows": 0,
                "row_order": "ascending",
                "cache_free": True,
                "functional_stages": ("empty quotient", "zero evidence increment"),
            }
            return 0.0, 0.0
        d, u = self.row_parameters(overlap, quality)
        inverse_d = 1.0 / d
        s1 = sz = su = suz = suu = np.float64(0.0)
        for row_index in range(z.size):
            s1 = np.float64(s1 + inverse_d[row_index])
            sz = np.float64(sz + z[row_index] * inverse_d[row_index])
            su = np.float64(su + u[row_index] * inverse_d[row_index])
            suz = np.float64(suz + u[row_index] * z[row_index] * inverse_d[row_index])
            suu = np.float64(suu + u[row_index] * u[row_index] * inverse_d[row_index])
        denominator = 1.0 + suu
        q_hat = MU * (sz - su * suz / denominator)
        j_hat = MU * MU * (s1 - su * su / denominator)
        if not np.isfinite(q_hat) or not np.isfinite(j_hat) or j_hat <= 0.0:
            raise FloatingPointError("CCIC Woodbury output is invalid")
        return q_hat, j_hat

    def train_batch(self, examples: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> float:
        gradients = _zeros_like(self.network.parameters)
        total_loss = 0.0
        for residual, overlap, quality in examples:
            d, u, (raw, cache) = self.row_parameters(overlap, quality, cache=True)
            covariance = np.diag(d) + np.outer(u, u)
            sign, logdet = np.linalg.slogdet(covariance)
            if sign <= 0.0:
                raise FloatingPointError("CCIC covariance is not positive definite")
            inverse = np.linalg.inv(covariance)
            solved = inverse @ residual
            total_loss += 0.5 * (logdet + float(residual @ solved) + residual.size * log(2.0 * pi))
            matrix_gradient = 0.5 * (inverse - np.outer(solved, solved))
            grad_d = np.diag(matrix_gradient)
            grad_u = (matrix_gradient + matrix_gradient.T) @ u
            raw_gradient = np.column_stack((grad_d * sigmoid(raw[:, 0]), grad_u * sigmoid(raw[:, 1])))
            _, sample_gradients = self.network.backward(raw_gradient, cache)
            _sum_gradients(gradients, sample_gradients)
        scale = 1.0 / len(examples)
        self.optimizer.step([gradient * scale for gradient in gradients])
        return total_loss * scale

    def state(self) -> dict:
        return self.network.state()


class ESSScalarModel:
    def __init__(self) -> None:
        self.raw = np.zeros(5, dtype=np.float64)
        self.optimizer = Adam([self.raw], learning_rate=3e-3)

    @staticmethod
    def _code_index(overlap: float) -> int:
        return {1.0: 0, 0.5: 1, 0.0: 2}[float(overlap)]

    def parameters_for(self, overlap: float) -> tuple[float, float]:
        index = self._code_index(overlap)
        nu = 1e-4 + float(softplus(self.raw[index:index + 1])[0])
        if overlap == 1.0:
            rho = 0.0
        else:
            beta_index = 3 if overlap == 0.5 else 4
            rho = 0.999 * float(sigmoid(self.raw[beta_index:beta_index + 1])[0])
        return nu, rho

    def fusion(self, z: np.ndarray, overlap: float) -> tuple[float, float]:
        if z.size == 0:
            return 0.0, 0.0
        nu, rho = self.parameters_for(overlap)
        denominator = nu * (1.0 + (z.size - 1) * rho)
        return MU * float(np.sum(z)) / denominator, MU * MU * z.size / denominator

    def train_batch(self, examples: list[tuple[np.ndarray, float]]) -> float:
        gradient = np.zeros_like(self.raw)
        total_loss = 0.0
        for residual, overlap in examples:
            m = residual.size
            index = self._code_index(overlap)
            nu, rho = self.parameters_for(overlap)
            correlation = (1.0 - rho) * np.eye(m, dtype=np.float64) + rho * np.ones((m, m), dtype=np.float64)
            covariance = nu * correlation
            sign, logdet = np.linalg.slogdet(covariance)
            if sign <= 0.0:
                raise FloatingPointError("ESS covariance is not positive definite")
            inverse = np.linalg.inv(covariance)
            solved = inverse @ residual
            total_loss += 0.5 * (logdet + float(residual @ solved) + m * log(2.0 * pi))
            matrix_gradient = 0.5 * (inverse - np.outer(solved, solved))
            grad_nu = float(np.sum(matrix_gradient * correlation))
            gradient[index] += grad_nu * float(sigmoid(self.raw[index:index + 1])[0])
            if overlap != 1.0:
                beta_index = 3 if overlap == 0.5 else 4
                grad_rho = float(np.sum(matrix_gradient * (nu * (np.ones((m, m)) - np.eye(m)))))
                beta_sigmoid = float(sigmoid(self.raw[beta_index:beta_index + 1])[0])
                gradient[beta_index] += grad_rho * 0.999 * beta_sigmoid * (1.0 - beta_sigmoid)
        scale = 1.0 / len(examples)
        self.optimizer.step([gradient * scale])
        return total_loss * scale

    def state(self) -> dict:
        return {"raw": self.raw.tolist()}


class RIStrongV2Model:
    def __init__(self, seed: int) -> None:
        # One shared module-2 network gives one continuous row-major Philox
        # parameter address range across both linear layers.
        self.row_network = MLP((6, 9, 2), seed, 2)
        if self.row_network.parameter_count != 83:
            raise AssertionError("RI-STRONG-v2 parameter count changed")
        self.parameters = self.row_network.parameters
        self.optimizer = Adam(self.parameters, learning_rate=3e-3)

    def forward(self, z: np.ndarray, overlap: float, t: int, k: int, cache: bool = False):
        if z.size == 0:
            if not cache:
                self.last_streaming_trace = {
                    "unique_rows": 0,
                    "row_order": "ascending",
                    "cache_free": True,
                    "functional_stages": ("empty quotient", "zero evidence increment"),
                }
            return (0.0, 0.0, None) if cache else (0.0, 0.0)
        rows = np.column_stack((z, np.full(z.size, overlap), np.ones(z.size), np.full(z.size, log(z.size)), np.full(z.size, t / 30.0), np.full(z.size, k / 5.0)))
        pooled = np.zeros(2, dtype=np.float64)
        if cache:
            raw_rows, row_cache = self.row_network.forward(rows, cache=True)
            transformed = raw_rows + np.tanh(raw_rows)
            for row_index in range(transformed.shape[0]):
                pooled[0] = np.float64(pooled[0] + transformed[row_index, 0])
                pooled[1] = np.float64(pooled[1] + transformed[row_index, 1])
        else:
            raw_rows = None
            row_cache = None
            for row_index in range(rows.shape[0]):
                raw_row = self.row_network.forward_row_streaming(rows[row_index])
                transformed_row = raw_row + np.tanh(raw_row)
                pooled[0] = np.float64(pooled[0] + transformed_row[0])
                pooled[1] = np.float64(pooled[1] + transformed_row[1])
            self.last_streaming_trace = {
                "unique_rows": int(rows.shape[0]),
                "row_order": "ascending",
                "cache_free": True,
                "functional_stages": ("6->9 linear", "SiLU", "9->2 linear", "r+tanh(r)", "mean", "decodes"),
            }
        pooled /= rows.shape[0]
        delta_ell = 8.0 * np.sinh(pooled[0])
        j_hat = 1e-4 + float(softplus(pooled[1:2])[0])
        if not np.isfinite(delta_ell) or not np.isfinite(j_hat):
            raise FloatingPointError("RI-STRONG-v2 decoded output is nonfinite")
        context = (raw_rows, pooled, row_cache, z.size)
        return (float(delta_ell), j_hat, context) if cache else (float(delta_ell), j_hat)

    def train_batch(self, examples: list[tuple[np.ndarray, float, int, int, float, float]]) -> float:
        gradients = _zeros_like(self.parameters)
        total_loss = 0.0
        normalizer = log(5.5)
        for z, overlap, t, k, target_delta, target_j in examples:
            delta, j_hat, (raw_rows, pooled, row_cache, m) = self.forward(z, overlap, t, k, cache=True)
            predicted_delta_target = pooled[0]
            expected_delta_target = np.arcsinh(target_delta / 8.0)
            predicted_j_target = log(1.0 + j_hat) / normalizer
            expected_j_target = log(1.0 + target_j) / normalizer
            delta_error = predicted_delta_target - expected_delta_target
            j_error = predicted_j_target - expected_j_target
            total_loss += 0.5 * (delta_error * delta_error + j_error * j_error)
            pooled_gradient = np.asarray(
                [delta_error, j_error * float(sigmoid(pooled[1:2])[0]) / ((1.0 + j_hat) * normalizer)],
                dtype=np.float64,
            )
            residual_derivative = 1.0 + 1.0 - np.tanh(raw_rows) ** 2
            row_output_gradient = np.repeat((pooled_gradient / m)[None, :], m, axis=0) * residual_derivative
            _, row_gradients = self.row_network.backward(row_output_gradient, row_cache)
            _sum_gradients(gradients, row_gradients)
        scale = 1.0 / len(examples)
        self.optimizer.step([gradient * scale for gradient in gradients])
        return total_loss * scale

    def state(self) -> dict:
        return self.row_network.state()


class InfoFlexModel:
    def __init__(self, seed: int) -> None:
        self.head = MLP((4, 11, 2), seed, 3)
        if self.head.parameter_count != 79:
            raise AssertionError("INFO-FLEX additional parameter count changed")
        self.optimizer = Adam(self.head.parameters, learning_rate=3e-3)

    def forward(self, ell_minus: float, q_hat: float, j_hat: float, k: int, cache: bool = False):
        inputs = np.asarray([[ell_minus, q_hat, j_hat, float(k)]], dtype=np.float64)
        raw, head_cache = self.head.forward(inputs, cache=True)
        ell = 8.0 * np.sinh(raw[0, 0])
        information = 1e-4 + float(softplus(raw[0, 1:2])[0])
        if not np.isfinite(ell) or not np.isfinite(information):
            raise FloatingPointError("INFO-FLEX decoded output is nonfinite")
        return (float(ell), information, (raw, head_cache)) if cache else (float(ell), information)

    def train_batch(self, examples: list[tuple[float, float, float, int, float, float]]) -> float:
        gradients = _zeros_like(self.head.parameters)
        total_loss = 0.0
        normalizer = log(5.5)
        for ell_minus, q_hat, j_hat, k, target_ell, target_j in examples:
            ell, predicted_j, (raw, cache) = self.forward(ell_minus, q_hat, j_hat, k, cache=True)
            ell_error = raw[0, 0] - np.arcsinh(target_ell / 8.0)
            j_error = log(1.0 + predicted_j) / normalizer - log(1.0 + target_j) / normalizer
            total_loss += 0.5 * (ell_error * ell_error + j_error * j_error)
            output_gradient = np.asarray(
                [[ell_error, j_error * float(sigmoid(raw[0, 1:2])[0]) / ((1.0 + predicted_j) * normalizer)]],
                dtype=np.float64,
            )
            _, sample_gradients = self.head.backward(output_gradient, cache)
            _sum_gradients(gradients, sample_gradients)
        scale = 1.0 / len(examples)
        self.optimizer.step([gradient * scale for gradient in gradients])
        return total_loss * scale

    def state(self) -> dict:
        return self.head.state()


class SharedActor:
    def __init__(self, seed: int) -> None:
        self.network = MLP((5, 32, 32, 4), seed, 4)
        self.optimizer = Adam(self.network.parameters, learning_rate=1e-3)

    @staticmethod
    def features(ell: float, j_next: float, t: int, k: int) -> np.ndarray:
        return np.asarray(
            [[np.clip(ell, -16.0, 16.0) / 16.0, log(1.0 + j_next) / log(5.5), t / 30.0, (30 - t) / 30.0, k / 5.0]],
            dtype=np.float64,
        )

    def logits(self, ell: float, j_next: float, t: int, k: int) -> np.ndarray:
        return self.network.forward(self.features(ell, j_next, t, k))[0]

    def probabilities(self, ell: float, j_next: float, t: int, k: int, legal_indices: tuple[int, ...]) -> np.ndarray:
        logits = self.logits(ell, j_next, t, k)
        probabilities = np.zeros(4, dtype=np.float64)
        shifted = logits[list(legal_indices)] - np.max(logits[list(legal_indices)])
        softmax = np.exp(shifted)
        softmax /= float(np.sum(softmax))
        probabilities[list(legal_indices)] = (1.0 - EPSILON_SUPPORT) * softmax + EPSILON_SUPPORT / len(legal_indices)
        return probabilities

    def train_batch(self, examples: list[tuple[float, float, int, int, int]]) -> float:
        accumulated_gradients = _zeros_like(self.network.parameters)
        loss_sum = np.float64(0.0)
        for ell, j_next, t, k, target in examples:
            feature = self.features(ell, j_next, t, k)
            logits, cache = self.network.forward(feature, cache=True)
            shifted = logits[0] - np.max(logits[0])
            probabilities = np.exp(shifted)
            probability_sum = np.float64(0.0)
            for action_index in range(probabilities.size):
                probability_sum = np.float64(probability_sum + probabilities[action_index])
            probabilities /= probability_sum
            loss_sum = np.float64(loss_sum - np.log(probabilities[target]))
            output_gradient = probabilities[None, :]
            output_gradient[0, target] -= 1.0
            _, sample_gradients = self.network.backward(output_gradient, cache)
            _sum_gradients(accumulated_gradients, sample_gradients)
        scale = 1.0 / len(examples)
        self.optimizer.step([gradient * scale for gradient in accumulated_gradients])
        return float(loss_sum * scale)

    def state(self) -> dict:
        return self.network.state()
