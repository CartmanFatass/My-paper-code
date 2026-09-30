"""Fixed episode-weighted ridge and supervised CPU MLP continuation values."""

import hashlib
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn

from .features import FEATURE_DIM, HORIZON


RIDGE_LAMBDA = .001
INIT_SEED = 29425000
SAMPLE_SEED = 29425001
UPDATES = 4096
BATCH_SIZE = 256


def _features(x):
    value = np.asarray(x)
    if value.dtype != np.dtype(np.float32) or value.ndim not in (1, 2) or value.shape[-1] != FEATURE_DIM or not np.isfinite(value).all():
        raise ValueError('values require finite float32 rows of805features')
    return value


def _network(seed):
    # Seed CPU only. No CUDA/global NumPy/Python RNG stream is repurposed.
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(int(seed))
        network = nn.Sequential(
            nn.Linear(FEATURE_DIM, 128, device='cpu', dtype=torch.float32), nn.ReLU(),
            nn.Linear(128, 128, device='cpu', dtype=torch.float32), nn.ReLU(),
            nn.Linear(128, 1, device='cpu', dtype=torch.float32),
        )
        nn.init.zeros_(network[-1].weight)
        nn.init.zeros_(network[-1].bias)
    return network


class ValueModel:
    def __init__(self, kind, *, coefficients=None, intercept=0., network=None):
        if kind not in ('ridge', 'neural'):
            raise ValueError('unknown value model kind')
        self.kind = kind
        if kind == 'ridge':
            self.coefficients = np.zeros(FEATURE_DIM, np.float64) if coefficients is None else np.asarray(coefficients, np.float64).copy()
            self.intercept = float(intercept)
            if self.coefficients.shape != (FEATURE_DIM,) or not np.isfinite(self.coefficients).all() or not np.isfinite(self.intercept):
                raise ValueError('malformed ridge parameters')
        else:
            if network is None:
                raise ValueError('neural model requires the fixed network')
            self.network = network.cpu().float().eval()

    def parameter_arrays(self):
        if self.kind == 'ridge':
            return dict(coefficients=self.coefficients.copy(), intercept=np.array(self.intercept, np.float64))
        return {name: value.detach().cpu().contiguous().numpy().copy()
                for name, value in self.network.state_dict().items()}

    def arrays(self):
        """Canonical learned numerical state for direct deterministic replay."""
        return self.parameter_arrays()

    def parameter_sha256(self):
        digest = hashlib.sha256()
        digest.update(self.kind.encode('ascii'))
        for name, array in self.parameter_arrays().items():
            digest.update(name.encode('ascii'))
            digest.update(str(array.dtype).encode('ascii'))
            digest.update(str(array.shape).encode('ascii'))
            digest.update(array.tobytes(order='C'))
        return digest.hexdigest()

    def raw_ticks(self, x):
        value = _features(x)
        scalar = value.ndim == 1
        if self.kind == 'ridge':
            prediction = HORIZON * (value.astype(np.float64) @ self.coefficients + self.intercept)
        else:
            with torch.inference_mode():
                prediction = (self.network(torch.from_numpy(value.copy())).squeeze(-1) * HORIZON).numpy().copy()
        return float(prediction) if scalar else prediction

    def evaluate(self, x, tick):
        if not isinstance(tick, (int, np.integer)) or isinstance(tick, (bool, np.bool_)) or not 0 <= tick <= HORIZON:
            raise ValueError('value tick outside0..256')
        if tick == HORIZON:
            return 0., 0.  # Terminal means no feature validation or model call.
        value = _features(x)
        if value.ndim != 1:
            raise ValueError('deployment evaluation requires one feature row')
        raw = self.raw_ticks(value)
        return raw, float(np.clip(raw, 0., HORIZON - int(tick)))


def initial_neural_model(*, init_seed=INIT_SEED):
    return ValueModel('neural', network=_network(init_seed))


def episode_weights(episode_ids):
    ids = np.asarray(episode_ids)
    if ids.ndim != 1 or not len(ids) or ids.dtype.kind not in 'iuUS':
        raise ValueError('episode IDs must be a nonempty integer/string vector')
    unique, inverse, counts = np.unique(ids, return_inverse=True, return_counts=True)
    weights = 1. / (len(unique) * counts[inverse].astype(np.float64))
    return weights, unique, inverse, counts


def _training(X, y_ticks, episode_ids):
    X = _features(X)
    y = np.asarray(y_ticks, dtype=np.float64)
    weights, unique, inverse, counts = episode_weights(episode_ids)
    if X.ndim != 2 or not len(X) or y.shape != (len(X),) or len(weights) != len(X) or not np.isfinite(y).all():
        raise ValueError('invalid paired regression rows, targets or episodes')
    return X, y / HORIZON, weights, unique, inverse, counts


def _flat(model):
    return np.concatenate([value.reshape(-1).astype(np.float64) for value in model.parameter_arrays().values()])


def _movement(before, after):
    difference = after - before
    return float(np.linalg.norm(difference)), float(np.max(np.abs(difference)))


def _stats(model, initial_hash, movement, X, unique, initial_mse, final_mse, wall, cpu):
    return dict(kind=model.kind, training_rows=len(X), eligible_episodes=len(unique),
                feature_dim=FEATURE_DIM, target_scale=HORIZON,
                parameter_count=int(len(_flat(model))),
                parameter_bytes=int(sum(value.nbytes for value in model.parameter_arrays().values())),
                initial_sha256=initial_hash, final_sha256=model.parameter_sha256(),
                parameter_movement_l2=movement[0], parameter_movement_max=movement[1],
                initial_weighted_mse=float(initial_mse), final_weighted_mse=float(final_mse),
                initial_prediction_rows=0, initial_prediction_kind='known-zero-output',
                final_prediction_rows=len(X), training_prediction_rows=len(X),
                wall_seconds=wall, cpu_seconds=cpu)


def fit_ridge(X, y_ticks, episode_ids):
    wall, cpu = time.perf_counter(), time.process_time()
    X, y, weights, unique, inverse, counts = _training(X, y_ticks, episode_ids)
    initial = ValueModel('ridge')
    initial_hash, before = initial.parameter_sha256(), _flat(initial)
    design = np.column_stack((np.ones(len(X)), X.astype(np.float64)))
    gram = design.T @ (weights[:, None] * design)
    gram[1:, 1:] += RIDGE_LAMBDA * np.eye(FEATURE_DIM, dtype=np.float64)
    rhs = design.T @ (weights * y)
    solution = np.linalg.solve(gram, rhs)
    model = ValueModel('ridge', coefficients=solution[1:], intercept=solution[0])
    prediction = model.raw_ticks(X) / HORIZON
    initial_mse = np.dot(weights, y**2)
    final_mse = np.dot(weights, (prediction - y)**2)
    movement = _movement(before, _flat(model))
    gradient = 2. * (gram @ solution - rhs)
    objective = final_mse + RIDGE_LAMBDA * np.square(solution[1:]).sum()
    stats = _stats(model, initial_hash, movement, X, unique, initial_mse, final_mse,
                   time.perf_counter() - wall, time.process_time() - cpu)
    stats.update(analytic_solves=1, optimizer_updates=0, minibatch_presentations=0,
                 ridge_lambda=RIDGE_LAMBDA, final_objective=float(objective))
    trace = dict(episode_ids=unique.copy(), episode_row_counts=counts.astype(np.int64), row_weights=weights,
                 sampled_rows=np.empty((0, 0), np.int64), final_prediction=prediction.copy(),
                 loss=np.array([objective], np.float64),
                 gradient_norm=np.array([np.linalg.norm(gradient)], np.float64),
                 initial_sha256=np.array(initial_hash), final_sha256=np.array(stats['final_sha256']),
                 parameter_movement_l2=np.array(movement[0]), parameter_movement_max=np.array(movement[1]))
    stats.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
    return model, stats, trace


def fit_neural(X, y_ticks, episode_ids, *, init_seed=INIT_SEED, sample_seed=SAMPLE_SEED,
               updates=UPDATES, batch_size=BATCH_SIZE):
    wall, cpu = time.perf_counter(), time.process_time()
    if type(updates) is not int or updates < 0 or type(batch_size) is not int or batch_size <= 0:
        raise ValueError('invalid synthetic/registered update or minibatch count')
    X, y, weights, unique, inverse, counts = _training(X, y_ticks, episode_ids)
    model = initial_neural_model(init_seed=init_seed)
    initial_hash, before = model.parameter_sha256(), _flat(model)
    rows_by_episode = [np.flatnonzero(inverse == episode) for episode in range(len(unique))]
    rng = np.random.Generator(np.random.PCG64(sample_seed))
    optimizer = torch.optim.Adam(model.network.parameters(), lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0.)
    features = torch.from_numpy(X.copy())
    targets = torch.from_numpy(y.astype(np.float32))
    sampled_rows = np.empty((updates, batch_size), np.int64)
    losses, norms, changes = (np.empty(updates, np.float64) for _ in range(3))
    model.network.train()
    previous = before
    for step in range(updates):
        for column in range(batch_size):
            episode = int(rng.integers(len(unique)))
            episode_rows = rows_by_episode[episode]
            sampled_rows[step, column] = episode_rows[int(rng.integers(len(episode_rows)))]
        row_indices = torch.from_numpy(sampled_rows[step])
        optimizer.zero_grad(set_to_none=True)
        prediction = model.network(features[row_indices]).squeeze(-1)
        loss = (prediction - targets[row_indices]).square().mean()
        if not torch.isfinite(loss):
            raise FloatingPointError('nonfinite regression loss')
        loss.backward()
        gradients = torch.cat([parameter.grad.detach().reshape(-1) for parameter in model.network.parameters()])
        if not torch.isfinite(gradients).all():
            raise FloatingPointError('nonfinite regression gradient')
        norms[step] = float(torch.linalg.vector_norm(gradients.to(torch.float64)))
        losses[step] = float(loss.detach())
        optimizer.step()
        current = _flat(model)
        if not np.isfinite(current).all():
            raise FloatingPointError('nonfinite regression parameters')
        changes[step] = _movement(previous, current)[0]
        previous = current
    optimizer.zero_grad(set_to_none=True)
    model.network.eval()
    final_prediction = model.raw_ticks(X) / HORIZON
    initial_mse = np.dot(weights, y**2)
    final_mse = np.dot(weights, (final_prediction.astype(np.float64) - y)**2)
    movement = _movement(before, _flat(model))
    stats = _stats(model, initial_hash, movement, X, unique, initial_mse, final_mse,
                   time.perf_counter() - wall, time.process_time() - cpu)
    stats.update(analytic_solves=0, optimizer_updates=updates, minibatch_presentations=updates * batch_size,
                 init_seed=int(init_seed), sample_seed=int(sample_seed), batch_size=batch_size,
                 learning_rate=.001, betas=[.9, .999], epsilon=1e-8, weight_decay=0.,
                 torch_threads=torch.get_num_threads())
    trace = dict(episode_ids=unique.copy(), episode_row_counts=counts.astype(np.int64), row_weights=weights,
                 sampled_rows=sampled_rows, final_prediction=final_prediction.copy(),
                 loss=losses, gradient_norm=norms,
                 parameter_change_l2=changes, initial_sha256=np.array(initial_hash),
                 final_sha256=np.array(stats['final_sha256']), parameter_movement_l2=np.array(movement[0]),
                 parameter_movement_max=np.array(movement[1]))
    stats.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
    return model, stats, trace


def save_model(path, model):
    payload = dict(schema_version=np.array(1, np.int64), kind=np.array(model.kind),
                   feature_dim=np.array(FEATURE_DIM, np.int64), horizon=np.array(HORIZON, np.int64),
                   parameter_sha256=np.array(model.parameter_sha256()))
    if model.kind == 'ridge':
        payload.update(model.parameter_arrays())
    else:
        payload.update({'network_' + name: value for name, value in model.parameter_arrays().items()})
    with Path(path).open('wb') as stream:
        np.savez_compressed(stream, **payload)


def load_model(path):
    with np.load(path, allow_pickle=False) as saved:
        if int(saved['schema_version']) != 1 or int(saved['feature_dim']) != FEATURE_DIM or int(saved['horizon']) != HORIZON:
            raise ValueError('checkpoint feature/schema contract mismatch')
        kind = str(saved['kind'])
        if kind == 'ridge':
            if saved['coefficients'].dtype != np.float64 or saved['intercept'].dtype != np.float64 or saved['intercept'].shape != ():
                raise ValueError('checkpoint ridge dtype/shape mismatch')
            model = ValueModel(kind, coefficients=saved['coefficients'], intercept=saved['intercept'])
        elif kind == 'neural':
            network = _network(0)
            state = {}
            for name, parameter in network.state_dict().items():
                value = saved['network_' + name]
                if value.dtype != np.float32 or value.shape != tuple(parameter.shape) or not np.isfinite(value).all():
                    raise ValueError('checkpoint network dtype/shape mismatch')
                state[name] = torch.from_numpy(value.copy())
            network.load_state_dict(state, strict=True)
            model = ValueModel(kind, network=network)
        else:
            raise ValueError('checkpoint kind mismatch')
        if model.parameter_sha256() != str(saved['parameter_sha256']):
            raise ValueError('checkpoint parameter digest mismatch')
    return model
