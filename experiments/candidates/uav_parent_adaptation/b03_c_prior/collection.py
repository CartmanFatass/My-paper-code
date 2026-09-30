"""Actual-history local C wrapper and complete decision/physics evidence."""

from collections import defaultdict
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_local_history.b01.study import native_reading
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from .policy import sample_actions
from .protocol import HORIZON, HOLD, clock, elapsed, identity


class LocalWrapper:
    """Only individual native observation rows enter the five C instances."""

    def __init__(self):
        self.controllers = [LocalController(history=False) for _ in range(5)]
        self.last = np.zeros((5, 3), dtype=np.float32)
        self.next_tick = 0

    def ingest(self, observation, tick):
        observation = np.asarray(observation, dtype=np.float32)
        if observation.shape != (5, 104) or not np.isfinite(observation).all():
            raise ValueError("five finite native local observation rows required")
        if tick != self.next_tick:
            raise ValueError("C must receive every primitive observation exactly once")
        self.next_tick += 1
        answers = [c.act(observation[i].copy(), tick) for i, c in enumerate(self.controllers)]
        nominal = np.stack([a[0] for a in answers])
        diagnostics = [a[1] for a in answers]
        nav = np.array([c._nav_index for c in self.controllers], dtype=np.int64)
        context = np.concatenate((observation, nominal, self.last,
                                  np.eye(10, dtype=np.float32)[nav]), axis=-1)
        return nominal, diagnostics, nav, context

    def sent(self, command):
        self.last[:] = command

    def counts(self):
        keys = self.controllers[0].counters
        return {"c_" + key: sum(c.counters[key] for c in self.controllers) for key in keys}


def collect_episode(env, actor, critic, *, arm, master, world_seed, training,
                    out, counts, horizon=HORIZON):
    """A smaller horizon is only for synthetic unit fixtures, never the runner."""
    if horizon <= 0 or horizon % HOLD or (training and arm != "train"):
        raise ValueError("invalid fixed-clock episode")
    if not training and arm not in ("C", "I", "Lg", "Ls"):
        raise ValueError("unknown evaluation arm")
    started = clock()
    wrapper = LocalWrapper()
    raw, macro = defaultdict(list), defaultdict(list)
    times = defaultdict(float)
    terminal = None
    # All truth stays in this evaluator/critic scope, outside wrapper/actor inputs.
    observation, info = env.reset(seed=world_seed)
    counts["explicit_resets"] += 1
    users = np.array(info["state_info"]["user_positions"], dtype=np.float64, copy=True)
    initial = np.array(info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
    before = initial.copy()
    state = np.array(info["state"], dtype=np.float32, copy=True)
    command = None
    failure = None
    try:
        for tick in range(horizon):
            stamp = time.perf_counter()
            nominal, diagnostics, nav, context = wrapper.ingest(observation, tick)
            times["c_seconds"] += time.perf_counter() - stamp
            raw["observations"].append(np.array(observation, dtype=np.float32, copy=True))
            raw["c_commands"].append(nominal)
            raw["c_nav"].append(nav)
            for key in ("fallback", "selected_index", "n_current", "n_visible_peers"):
                raw["c_" + key].append([d[key] for d in diagnostics])
            if tick % HOLD == 0:
                index = np.array([d["selected_index"] for d in diagnostics], dtype=np.int64)
                if not np.array_equal(COMMANDS[index], nominal):
                    raise RuntimeError("C label and nominal command disagree")
                critic_row = critic_features(state, wrapper.last, np.zeros(5, dtype=np.int64))
                stamp = time.perf_counter()
                with torch.no_grad():
                    logits = actor(torch.from_numpy(context), torch.from_numpy(index))
                    action, log_prob, entropy, seeds = sample_actions(
                        logits, domain="train" if training else "eval", master=master,
                        world_seed=world_seed, macro_index=tick // HOLD,
                        greedy=arm in ("C", "Lg"))
                    value = float(critic(torch.from_numpy(critic_row)).item()) if training else 0.0
                times["actor_critic_seconds"] += time.perf_counter() - stamp
                if arm == "C" and not np.array_equal(action.numpy(), index):
                    raise RuntimeError("initial greedy policy is not exactly C")
                command = COMMANDS[action.numpy()].copy()
                key = "train_actor_rows" if training else (
                    "identity_shadow_rows" if arm == "C" else "eval_actor_rows")
                counts[key] += 5
                if training:
                    counts["train_critic_rows"] += 1
                for key, val in dict(context=context, c_index=index, action=action.numpy(),
                                     log_prob=log_prob.numpy(), logits=logits.numpy(),
                                     entropy=entropy.numpy(), values=value, critic=critic_row,
                                     native_state=state.copy(), seeds=(np.full(5, -1, np.int64)
                                     if seeds is None else seeds.numpy()),
                                     candidate_scores=np.stack([d["scores"] for d in diagnostics]),
                                     candidate_service=np.stack([d["served_candidates"] for d in diagnostics])).items():
                    macro[key].append(val)
            if command is None or command.dtype != np.float32:
                raise RuntimeError("missing held command")
            raw["commands"].append(command.copy())
            counts["native_step_calls"] += 1
            stamp = time.perf_counter()
            next_obs, _mean_reward, terminated, truncated, next_info = env.step(command.copy())
            times["native_step_seconds"] += time.perf_counter() - stamp
            counts["team_steps"] += 1
            counts["train_team_steps" if training else "eval_team_steps"] += 1
            reward, service, quality = native_reading(next_info)
            after = np.array(next_info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
            for key, val in dict(reward=reward, served=service, sinr_quality=quality,
                                 post_positions=after, displacements=after - before).items():
                raw[key].append(val)
            wrapper.sent(command)
            if bool(terminated or truncated) != (tick + 1 == horizon):
                raise RuntimeError(f"unexpected episode boundary at {tick + 1}/{horizon}")
            observation, before = next_obs, after
            state = np.array(next_info["next_state"], dtype=np.float32, copy=True)
        terminal = np.array(observation, dtype=np.float32, copy=True)
    except BaseException as exc:
        failure = exc
    finally:
        for key, number in wrapper.counts().items():
            counts[key] += number
        arrays = {key: np.asarray(value) for key, value in raw.items()}
        arrays.update({"macro_" + key: np.asarray(value) for key, value in macro.items()})
        arrays.update(true_users=users, initial_positions=initial,
                      terminal_observation=(np.empty((0, 104), np.float32) if terminal is None else terminal))
        if failure is None:
            arrays["macro_reward"] = arrays["reward"].reshape(-1, HOLD).sum(axis=1)
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = time.perf_counter()
        np.savez_compressed(path, **arrays)
        times["storage_seconds"] += time.perf_counter() - stamp
    if failure is not None:
        raise failure
    counts["train_episodes" if training else "eval_episodes"] += 1
    physical = np.linalg.norm(arrays["displacements"], axis=-1)
    before_all = np.concatenate((initial[None], arrays["post_positions"][:-1]), axis=0)
    nominal_after = np.clip(before_all + 30 * arrays["c_commands"], [0, 0, 50], [1000, 1000, 150])
    departure = np.any(arrays["commands"] != arrays["c_commands"], axis=-1)
    applied_departure = np.any(arrays["post_positions"] != nominal_after, axis=-1)
    row = dict(arm=arm, master=master, world_seed=world_seed, training=training,
               J=float(arrays["reward"].mean()), mean_served=float(arrays["served"].mean()),
               mean_quality=float(arrays["sinr_quality"].mean()),
               zero_service_ticks=int((arrays["served"] == 0).sum()),
               mean_agent_path_m=float(physical.sum(axis=0).mean()),
               requested_departure_decisions=int(departure[::HOLD].sum()),
               applied_departure_agent_ticks=int(applied_departure.sum()),
               boundary_alias_agent_ticks=int((departure & ~applied_departure).sum()),
               mean_entropy=float(arrays["macro_entropy"].mean()),
               mean_c_probability=float(torch.softmax(torch.from_numpy(arrays["macro_logits"]), -1)
                                         .gather(-1, torch.from_numpy(arrays["macro_c_index"])[..., None]).mean()),
               fallback_agent_decisions=int(arrays["c_fallback"][::HOLD].sum()),
               counters=wrapper.counts(), resources=elapsed(started), component_wall=times,
               probability_role=("sampled_behavior" if training or arm in ("I", "Ls")
                                 else "categorical_reference_only_deterministic_behavior"),
               raw=identity(path))
    names = dict(context="context", c_index="c_index", action="action",
                 log_prob="logp", values="value", critic="critic")
    episode = {names[key]: torch.from_numpy(np.asarray(value)) for key, value in macro.items()
               if key in names}
    episode["reward"] = torch.from_numpy(arrays["macro_reward"])
    return episode, row
