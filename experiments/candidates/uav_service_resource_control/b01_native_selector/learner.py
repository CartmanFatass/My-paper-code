"""Fixed B01 CPU FP32 finite-mission Double-DQN and immutable replay traces.

This module has no runner or native dependencies. The mission owner supplies the
three published seeds and marks *all* native endings, including H3000, terminal.
Checkpoint loading is an evidence-reconstruction facility, not a resume policy.
"""
import copy
import hashlib
import json
import math

import numpy as np
import torch
from torch import nn


INPUT_DIM = 327
CAPACITY = 12800
BATCH_SIZE = 64
WARMUP_MISSIONS = 16
TARGET_INTERVAL = 200
BLOCK_TICKS = 30


def _digest(value):
    """Stable content hash, independent of torch.save's container metadata."""
    digest = hashlib.sha256()

    def visit(item):
        if isinstance(item, torch.Tensor):
            visit(item.detach().cpu().contiguous().numpy())
        elif isinstance(item, np.ndarray):
            digest.update(b"array:")
            digest.update(str(item.dtype).encode())
            digest.update(json.dumps(item.shape).encode())
            digest.update(item.tobytes(order="C"))
        elif isinstance(item, dict):
            digest.update(b"dict:")
            for key in sorted(item, key=lambda x: (type(x).__name__, str(x))):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            digest.update(b"sequence:")
            for entry in item:
                visit(entry)
        else:
            digest.update(json.dumps(item, sort_keys=True, allow_nan=False).encode())
            digest.update(b";")

    visit(value)
    return digest.hexdigest()


def _features(value):
    result = np.asarray(value, dtype=np.float32)
    if result.shape != (INPUT_DIM,) or not np.isfinite(result).all():
        raise ValueError("B01 features must be finite FP32[327]")
    return result.copy()


def _network(seed):
    # Linear's unavoidable default initialization is sandboxed. All retained
    # weights are subsequently drawn from the dedicated CPU generator.
    with torch.random.fork_rng(devices=[]):
        model = nn.Sequential(
            nn.Linear(INPUT_DIM, 64, device="cpu", dtype=torch.float32), nn.ReLU(),
            nn.Linear(64, 64, device="cpu", dtype=torch.float32), nn.ReLU(),
            nn.Linear(64, 2, device="cpu", dtype=torch.float32))
    generator = torch.Generator(device="cpu").manual_seed(int(seed))
    with torch.no_grad():
        for layer in (model[0], model[2]):
            bound = math.sqrt(6 / layer.in_features)
            layer.weight.uniform_(-bound, bound, generator=generator)
            layer.bias.zero_()
        model[4].weight.zero_()
        model[4].bias.zero_()
    return model


# dtype and trailing shape also define empty exports; NPZ requires no pickling.
_SCHEMA = {
    "action_features": (np.float32, (327,)), "action_step": (np.int64, ()),
    "action_h_eligible": (np.bool_, ()), "action_action": (np.int64, ()),
    "action_q_values": (np.float32, (2,)), "action_epsilon": (np.float64, ()),
    "action_exploration_draws": (np.float64, (2,)),
    "action_explored": (np.bool_, ()), "action_updates": (np.int64, ()),
    "action_postwarmup_transitions": (np.int64, ()),
    "action_replay_size": (np.int64, ()), "action_online_digest": ("U64", ()),
    "reward_step": (np.int64, ()), "reward_native_J": (np.float64, ()),
    "reward_terminal": (np.bool_, ()),
    "transition_id": (np.int64, ()), "transition_slot": (np.int64, ()),
    "transition_step": (np.int64, ()), "transition_end_step": (np.int64, ()),
    "transition_features": (np.float32, (327,)), "transition_action": (np.int64, ()),
    "transition_next_features": (np.float32, (327,)),
    "transition_next_h_eligible": (np.bool_, ()), "transition_terminal": (np.bool_, ()),
    "transition_reward64": (np.float64, ()), "transition_reward32": (np.float32, ()),
    "transition_update_due": (np.bool_, ()), "transition_update_skipped": (np.bool_, ()),
    "update_number": (np.int64, ()), "update_transition_id": (np.int64, ()),
    "update_indices": (np.int64, (64,)), "update_transition_ids": (np.int64, (64,)),
    "update_selected_q": (np.float32, (64,)), "update_targets": (np.float32, (64,)),
    "update_next_actions": (np.int64, (64,)), "update_loss": (np.float64, ()),
    "update_gradient_norm": (np.float64, ()), "update_target_copy": (np.bool_, ()),
    "update_online_before": ("U64", ()), "update_online_after": ("U64", ()),
    "update_target_before": ("U64", ()), "update_target_after": ("U64", ()),
    "update_optimizer_before": ("U64", ()), "update_optimizer_after": ("U64", ()),
}


class Learner:
    def __init__(self, *, init_seed, exploration_seed, replay_seed):
        self.seeds = dict(init_seed=int(init_seed), exploration_seed=int(exploration_seed),
                          replay_seed=int(replay_seed))
        self.online = _network(init_seed)
        self.target = copy.deepcopy(self.online)
        self.target.requires_grad_(False)
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=3e-4,
                                          betas=(.9, .999), eps=1e-8,
                                          weight_decay=0, foreach=False)
        self.exploration_rng = np.random.Generator(np.random.PCG64(exploration_seed))
        self.replay_rng = np.random.Generator(np.random.PCG64(replay_seed))
        self.replay = {
            "features": np.zeros((CAPACITY, INPUT_DIM), np.float32),
            "next_features": np.zeros((CAPACITY, INPUT_DIM), np.float32),
            "action": np.zeros(CAPACITY, np.int64),
            "reward": np.zeros(CAPACITY, np.float32),
            "terminal": np.zeros(CAPACITY, np.bool_),
            "next_h_eligible": np.zeros(CAPACITY, np.bool_),
            "id": np.full(CAPACITY, -1, np.int64),
        }
        self.replay_size = self.transitions = self.postwarmup_transitions = 0
        self.updates = self.skipped_updates = self.training_missions = 0
        self.training_ticks = self.evaluation_ticks = 0
        self.episode_index = None
        self.training = False
        self.episode_ended = True
        self.pending = None
        self.inference_only = False
        self._rows = {key: [] for key in _SCHEMA}

    def counts(self):
        return {key: getattr(self, key) for key in (
            "replay_size", "transitions", "postwarmup_transitions", "updates",
            "skipped_updates", "training_missions", "training_ticks", "evaluation_ticks")}

    def digests(self):
        return dict(online=_digest(self.online.state_dict()),
                    target=_digest(self.target.state_dict()),
                    optimizer=_digest(self.optimizer.state_dict()))

    def start_episode(self, index: int, training: bool):
        if not self.episode_ended or self.pending is not None:
            raise RuntimeError("previous native mission has not ended")
        if type(index) is not int or index < 0:
            raise ValueError("mission index must be a nonnegative integer")
        if training and self.inference_only:
            raise RuntimeError("compact noninitial checkpoint is inference-only")
        if training and (index != self.training_missions or index >= 128):
            raise ValueError("training must use actual mission indices 0..127 in order")
        self.episode_index, self.training = index, bool(training)
        self.episode_ended = False
        self._rows = {key: [] for key in _SCHEMA}
        if training:
            self.training_missions += 1

    def _log(self, prefix, **values):
        for key, value in values.items():
            self._rows[prefix + "_" + key].append(copy.deepcopy(value))

    @torch.no_grad()
    def decide(self, features: np.ndarray, h_eligible: bool, step: int) -> dict:
        if self.episode_index is None or self.episode_ended:
            raise RuntimeError("decision outside an active mission")
        x = _features(features)
        expected_step = len(self._rows["reward_step"])
        if type(step) is not int or step != expected_step or step % BLOCK_TICKS or step >= 3000:
            raise ValueError("decision requires the next real 30-tick boundary")
        if len(self._rows["action_step"]) >= 100:
            raise ValueError("more than 100 native blocks")
        if self.pending is not None:
            if len(self.pending["rewards"]) != BLOCK_TICKS:
                raise RuntimeError("nonterminal transition needs exactly 30 executed ticks")
            # Enable gradients only for the due update, before this action's Q.
            with torch.enable_grad():
                self._close(x, bool(h_eligible), False)
        elif step != 0:
            raise RuntimeError("missing previous block")
        q = self.online(torch.from_numpy(x)).numpy().copy()
        if not np.isfinite(q).all():
            raise FloatingPointError("nonfinite online Q")
        epsilon = (1. if self.episode_index < WARMUP_MISSIONS else
                   max(.05, 1 - .95 * self.postwarmup_transitions / 6400)) if self.training else 0.
        valid = np.arange(2 if h_eligible else 1)
        draws = self.exploration_rng.random(2) if self.training else np.full(2, np.nan)
        explored = self.training and draws[0] < epsilon
        action = int(valid[math.floor(draws[1] * len(valid))] if explored else valid[np.argmax(q[valid])])
        diagnostics = dict(action=action, q_values=q.copy(), epsilon=epsilon,
                           exploration_draws=draws.copy(), explored=bool(explored),
                           updates=self.updates, postwarmup_transitions=self.postwarmup_transitions,
                           replay_size=self.replay_size, online_digest=_digest(self.online.state_dict()))
        self._log("action", features=x, step=step, h_eligible=bool(h_eligible), **diagnostics)
        self.pending = dict(features=x, action=action, step=step, rewards=[])
        return {**diagnostics, "transitions": self.transitions}

    def observe_reward(self, native_J: float, terminal: bool):
        if self.pending is None or self.episode_ended:
            raise RuntimeError("reward without an executed pending action")
        reward = float(native_J)
        if not math.isfinite(reward):
            raise ValueError("native J must be finite")
        if len(self.pending["rewards"]) >= BLOCK_TICKS:
            raise RuntimeError("next boundary must be decided before another native tick")
        step = self.pending["step"] + len(self.pending["rewards"])
        if step >= 2999 and not terminal:
            raise ValueError("H3000 truncation must be terminal; no horizon bootstrap")
        self.pending["rewards"].append(reward)
        self._log("reward", step=step, native_J=reward, terminal=bool(terminal))
        if self.training:
            self.training_ticks += 1
        else:
            self.evaluation_ticks += 1
        if terminal:
            self._close(np.zeros(INPUT_DIM, np.float32), False, True)
            self.episode_ended = True

    def _close(self, next_features, next_h_eligible, terminal):
        old = self.pending
        if not old["rewards"]:
            raise RuntimeError("cannot fabricate a zero-tick transition")
        reward64 = math.fsum(old["rewards"]) / BLOCK_TICKS
        reward32 = np.float32(reward64)
        if not np.isfinite(reward32):
            raise FloatingPointError("block reward overflows FP32")
        slot, transition_id = -1, -1
        due = self.training and self.episode_index >= WARMUP_MISSIONS
        if self.training:
            transition_id = self.transitions
            slot = transition_id % CAPACITY
            for key, value in dict(features=old["features"], action=old["action"],
                                   reward=reward32, next_features=next_features,
                                   next_h_eligible=next_h_eligible, terminal=terminal,
                                   id=transition_id).items():
                self.replay[key][slot] = value
            self.transitions += 1
            self.replay_size = min(CAPACITY, self.replay_size + 1)
            if due:
                self.postwarmup_transitions += 1
        skipped = due and self.replay_size < BATCH_SIZE
        self._log("transition", id=transition_id, slot=slot, step=old["step"],
                  end_step=old["step"] + len(old["rewards"]), features=old["features"],
                  action=old["action"], next_features=next_features,
                  next_h_eligible=next_h_eligible, terminal=terminal,
                  reward64=reward64, reward32=reward32, update_due=due, update_skipped=skipped)
        if skipped:
            self.skipped_updates += 1
        elif due:
            self._update(transition_id)
        self.pending = None

    def _optimize(self, indices):
        """One real Adam step; separate from sampling/clocks for bounded clock tests."""
        batch = {key: torch.from_numpy(value[indices].copy()) for key, value in self.replay.items()}
        selected = self.online(batch["features"]).gather(1, batch["action"][:, None]).squeeze(1)
        with torch.no_grad():
            next_q = self.online(batch["next_features"])
            next_q[:, 1].masked_fill_(~batch["next_h_eligible"], -torch.inf)
            next_actions = next_q.argmax(dim=1)
            bootstrap = self.target(batch["next_features"]).gather(1, next_actions[:, None]).squeeze(1)
            targets = batch["reward"] + torch.where(batch["terminal"], torch.zeros_like(bootstrap), bootstrap)
        loss = nn.functional.smooth_l1_loss(selected, targets, reduction="mean", beta=1.)
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite Double-DQN loss")
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = nn.utils.clip_grad_norm_(self.online.parameters(), 10., error_if_nonfinite=True)
        self.optimizer.step()
        return dict(selected_q=selected.detach().numpy().copy(), targets=targets.numpy().copy(),
                    next_actions=next_actions.numpy().copy(), loss=float(loss.detach()),
                    gradient_norm=float(norm.detach()))

    def _update(self, transition_id):
        indices = self.replay_rng.choice(self.replay_size, size=BATCH_SIZE, replace=False)
        before = self.digests()
        result = self._optimize(indices)
        self.updates += 1
        target_copy = self.updates % TARGET_INTERVAL == 0
        if target_copy:
            self.target.load_state_dict(self.online.state_dict())
        after = self.digests()
        self._log("update", number=self.updates, transition_id=transition_id,
                  indices=indices, transition_ids=self.replay["id"][indices],
                  target_copy=target_copy, **result,
                  online_before=before["online"], online_after=after["online"],
                  target_before=before["target"], target_after=after["target"],
                  optimizer_before=before["optimizer"], optimizer_after=after["optimizer"])

    def episode_arrays(self):
        """Snapshot this mission only, including all chronological reconstruction inputs."""
        return {key: np.asarray(self._rows[key], dtype=dtype).reshape((-1,) + shape).copy()
                for key, (dtype, shape) in _SCHEMA.items()}

    def state(self, include_replay=True):
        """Detached checkpoint. Compact milestones omit replay and mission trace copies.

        Compact initial state can seed chronological reconstruction. A noninitial
        compact state can only deploy inference; it cannot continue training.
        """
        if not include_replay and (self.pending is not None or not self.episode_ended):
            raise RuntimeError("compact checkpoints require initial/completed mission state")
        result = dict(
            version=1, seeds=self.seeds, online=self.online.state_dict(),
            target=self.target.state_dict(), optimizer=self.optimizer.state_dict(),
            exploration_rng=self.exploration_rng.bit_generator.state,
            replay_rng=self.replay_rng.bit_generator.state,
            counts=self.counts(), episode_index=self.episode_index, training=self.training,
            episode_ended=self.episode_ended, inference_only=self.inference_only)
        if include_replay:
            result.update(replay=self.replay, pending=self.pending, rows=self._rows)
        return copy.deepcopy(result)

    def load_state(self, state):
        """Restore exact evidence state, including pending reward accumulation and logs."""
        state = copy.deepcopy(state)
        if state["version"] != 1 or state["seeds"] != self.seeds:
            raise ValueError("B01 checkpoint version/seed mismatch")
        self.online.load_state_dict(state["online"])
        self.target.load_state_dict(state["target"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.exploration_rng.bit_generator.state = state["exploration_rng"]
        self.replay_rng.bit_generator.state = state["replay_rng"]
        if "replay" in state:
            self.replay = state["replay"]
        else:
            for key, value in self.replay.items():
                value.fill(-1 if key == "id" else 0)
        for key, value in state["counts"].items():
            setattr(self, key, value)
        for key in ("episode_index", "training", "episode_ended"):
            setattr(self, key, state[key])
        self.pending = state.get("pending")
        self._rows = state.get("rows", {key: [] for key in _SCHEMA})
        self.inference_only = state["inference_only"] or (
            "replay" not in state and self.transitions > 0)
