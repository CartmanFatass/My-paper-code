"""B03 learner "GAS-HMASD": HMASD's coordinator assigning grounded anchor labels to the SET actor.

What changes relative to ``HMASDAgent`` (every other path -- coordinator, its optimizer, the
high-level ordinary-segment buffer and PPO, the critic, the low-level PPO -- is HMASD's):

- ``GASSkillDiscoverer`` (subclass of ``hmasd/networks.py::SkillDiscoverer``): the actor input is
  the CF input (own obs 365 | state 306 | 8 x obs 365 | ego 8) plus a six-number anchor block
  ``[anchor x/area, anchor y/area, rel x/area, rel y/area, dist/area, is_free]`` = 3605, built at
  the single application point ``_apply_central_input`` from the stored anchors, the label and
  the *current* observation's own xy (``obs[..., 0:2]``, ``b01/observation.py``
  ``ObservationLayout.own``).  FREE (label 8) gives zeros with ``is_free = 1``.  FiLM stays on
  the 9-wide label one-hot (``R_Actor``).  The raw 18 anchor numbers do not enter the actor.
- The held central snapshot row is ``state 306 | anchors 18 | labels 8`` = 332
  (``GASHMASDAgent._refresh_central_snapshots``), stored per step in the rollout buffer
  (``GASRolloutBuffer``, the core buffer with that one width), so replay reads the stored anchors
  and labels; replay never recomputes k-means.  The per-agent central input is
  ``state | anchors | own label | 8 x obs | ego`` = 3253 on both paths
  (``_central_actor_input`` acting, ``_central_actor_input_from_replay`` replay).
- Why the label rides with the snapshot: ``hmasd/agent.py::update_discoverer_from_rollout``
  calls ``skill_discoverer._apply_central_input(obs_seq, central_input_seq)`` without the labels
  (``evaluate_sequence`` has no caller in the update), so the replayed actor input can only get
  the label from the stored snapshot.  Acting ``forward`` and ``evaluate_sequence`` pass their
  labels too and are refused if they differ from the stored one.

Order of operations in one ``step`` (``hmasd/agent.py::HMASDAgent.step``, off route):
1. new lanes get ``env_timers = 0`` and placeholder skills;
2. ``_batched_assign_skills``: lanes with ``env_steps % k == 0 | dones | invalid skills`` are
   re-decided by the coordinator on this step's state/observations; their timer is set to 0,
   every other lane's timer is incremented (so ``timer == 0`` after this call <=> decided now);
   ``env_agent_skills`` then holds the labels just decoded;
3. ``_refresh_central_snapshots(states, observations, timer == 0 | ~valid)``: for each refreshed
   lane this class computes the anchors from the *same* ``states`` row the coordinator decided
   on and stores them with ``env_agent_skills[lane]``; a refreshed lane whose timer is not 0
   (which would pair anchors of one step with labels of another) is refused.  A lane reset
   (``reset_env_state``) clears the snapshot and marks the skills invalid, and the collector
   passes ``dones`` for that lane at the next step, so the first step after a reset is a decision
   step and refreshes; with ``ordinary_completed_segments = True`` ``clear_buffers`` keeps
   ``env_timers`` and the snapshots, so a lane live at a rollout boundary keeps its cadence;
4. ``_batched_select_action``: the actor reads the held snapshot (``_central_actor_input``) with
   ``agent_skills`` = the labels of step 2, cross-checked against the stored labels.
Between decisions the labels and the snapshot are both held, so the stored labels equal the
FiLM labels at every step.

Decision log: at every team decision one row ``{env, step, labels[8], anchors[9][2],
own_xy[8][2]}`` (anchors float64 area-normalised, own xy = the decision step's observation
``obs[:, 0:2]``) is appended to ``decision_log``; ``b03/training.py`` flushes it per rollout.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from torch.optim import Adam

from hmasd.agent import HMASDAgent
from hmasd.logging import main_logger
from hmasd.networks import SkillDiscoverer
from hmasd.utils import RolloutBuffer

from .anchors import ANCHOR_DIM, FREE_LABEL, N_LABELS, anchors_from_state
from .configuration import (
    ANCHOR_BLOCK_WIDTH, actor_input_width, central_input_width, snapshot_width,
)


def check_gas_config(config) -> None:
    """The configuration contract this learner is defined for (``make_b03_config``)."""
    problems = []
    if not bool(getattr(config, "use_central_snapshot_in_flat_actor", False)):
        problems.append("use_central_snapshot_in_flat_actor must be True")
    if int(config.n_z) != N_LABELS or int(config.n_Z) != 1:
        problems.append(f"n_z must be {N_LABELS} and n_Z 1")
    if bool(getattr(config, "use_obsnorm", False)) or bool(getattr(config, "use_statenorm", True)):
        # The update path would broadcast a state_dim-wide state_norm over the 332-wide row.
        problems.append("observation/state normalizers must be off")
    if getattr(config, "central_snapshot_state_affine", None) is not None:
        problems.append("central_snapshot_state_affine is not supported")
    if bool(getattr(config, "use_compact_in_low_level_actor", False)):
        problems.append("the compact low-level context is not supported")
    if str(getattr(config, "policy_interruption_mode", "off")) != "off" or bool(
            getattr(config, "use_horizon_window", False)):
        problems.append("only the ordinary fixed-k route is supported")
    if bool(getattr(config, "use_lr_decay", False)):
        problems.append("LR schedulers would bind the replaced optimizers")
    if not bool(getattr(config, "ordinary_completed_segments", False)):
        problems.append("ordinary_completed_segments must be True")
    if bool(getattr(config, "disable_high_level_training", False)):
        problems.append("high-level training must be on")
    if int(config.state_dim) != 306 or int(config.n_agents) != 8:
        problems.append("S7-S2 state (306) and 8 UAVs expected")
    if problems:
        raise ValueError("GAS configuration refused: " + "; ".join(problems))


class GASSkillDiscoverer(SkillDiscoverer):
    """``SkillDiscoverer`` whose actor reads the CF input plus the anchor block (3605 wide)."""

    def __init__(self, config, logger=None, device=None):
        check_gas_config(config)
        # ``SkillDiscoverer.__init__`` assigns ``central_input_dim`` and sizes the actor from
        # ``obs_dim + central_input_dim``; the property below adds the anchor block to that width
        # so the actor, film, GRU, head and critic are built in one pass in the base order.
        super().__init__(config, logger=logger, device=device)
        self.gas_state_dim = int(config.state_dim)
        self.gas_n_agents = int(config.n_agents)
        self.gas_central_input_dim = central_input_width(config)
        first = next(module for module in self.actor.base.modules()
                     if isinstance(module, torch.nn.Linear))
        if first.in_features != actor_input_width(config):
            raise RuntimeError(f"GAS actor input width {first.in_features} != "
                               f"{actor_input_width(config)}")

    @property
    def central_input_dim(self):
        """Width the actor input adds to the observation: CF width (state | 8 x obs | ego) + 6."""
        return self._cf_central_input_dim + ANCHOR_BLOCK_WIDTH

    @central_input_dim.setter
    def central_input_dim(self, value):
        self._cf_central_input_dim = int(value)

    def _apply_central_input(self, tensor, central_input, agent_skill=None):
        """``cat[obs, state, 8 x obs, ego, block]`` from the per-agent central input (3253 wide).

        The label is read from the central input (stored with the snapshot); when
        ``agent_skill`` is given it must equal that label.
        """
        if central_input is None:
            raise ValueError("the GAS actor requires a central input")
        if not torch.is_tensor(central_input):
            central_input = torch.as_tensor(central_input, dtype=tensor.dtype, device=tensor.device)
        else:
            central_input = central_input.to(device=tensor.device, dtype=tensor.dtype)
        if central_input.shape[-1] != self.gas_central_input_dim:
            raise ValueError(f"GAS central input must have last dimension "
                             f"{self.gas_central_input_dim}, got {tuple(central_input.shape)}")
        if central_input.shape[:-1] != tensor.shape[:-1]:
            raise ValueError(f"central input batch shape {tuple(central_input.shape[:-1])} does "
                             f"not match the observation batch shape {tuple(tensor.shape[:-1])}")
        state_end = self.gas_state_dim
        anchors_end = state_end + ANCHOR_DIM
        state = central_input[..., :state_end]
        anchors = central_input[..., state_end:anchors_end]
        label_value = central_input[..., anchors_end]
        rest = central_input[..., anchors_end + 1:]
        label = label_value.long()
        invalid = ((label.to(label_value.dtype) != label_value) | (label < 0)
                   | (label >= N_LABELS))
        if bool(invalid.any()):
            raise ValueError("GAS central input carries an invalid anchor label")
        if agent_skill is not None:
            skill = torch.as_tensor(agent_skill, device=label.device).long().reshape(label.shape)
            if not torch.equal(skill, label):
                raise RuntimeError("actor label differs from the label stored with the snapshot")
        anchors = anchors.reshape(*anchors.shape[:-1], N_LABELS, 2)
        index = label.unsqueeze(-1).unsqueeze(-1).expand(*label.shape, 1, 2)
        assigned = torch.gather(anchors, -2, index).squeeze(-2)
        free = (label == FREE_LABEL).unsqueeze(-1)
        zeros = torch.zeros_like(assigned)
        absolute = torch.where(free, zeros, assigned)
        relative = torch.where(free, zeros, assigned - tensor[..., 0:2])
        rel_x, rel_y = relative[..., 0:1], relative[..., 1:2]
        distance = torch.sqrt(rel_x * rel_x + rel_y * rel_y)
        block = torch.cat([absolute, relative, distance, free.to(tensor.dtype)], dim=-1)
        return torch.cat([tensor, state, rest, block], dim=-1)

    def forward(self, observation, agent_skill, hidden_state, deterministic=False,
                compact_context=None, central_input=None):
        observation = self._apply_compact_context(observation, compact_context,
                                                  self.actor_context_adapter)
        observation = self._apply_central_input(observation, central_input, agent_skill)
        masks = torch.ones(observation.size(0), 1, device=observation.device)
        actions, log_probs, new_hidden = self.actor(observation, hidden_state, masks, agent_skill,
                                                    deterministic=deterministic)
        return actions, log_probs, None, new_hidden

    def evaluate_sequence(self, observations_seq, agent_skills_seq, actions_seq, global_states_seq,
                          team_skills_seq, initial_hxs=None, dones_seq=None,
                          initial_critic_hxs=None, compact_context_seq=None,
                          central_input_seq=None):
        """``SkillDiscoverer.evaluate_sequence`` with the labels passed to the application point."""
        T, B, _ = observations_seq.shape
        if dones_seq is None:
            dones_seq = torch.zeros((T, B), device=observations_seq.device)
        if dones_seq.dim() > 2:
            dones_seq = dones_seq.squeeze(-1)
        if dones_seq.shape != (T, B):
            raise ValueError(f"dones_seq must have shape {(T, B)} or {(T, B, 1)}, "
                             f"got {tuple(dones_seq.shape)}")
        masks = torch.ones_like(dones_seq, dtype=torch.float32)
        if T > 1:
            masks[1:] = 1.0 - dones_seq[:-1].float()
        actor_observations = self._apply_central_input(
            self._apply_compact_context(observations_seq, compact_context_seq,
                                        self.actor_context_adapter),
            central_input_seq, agent_skills_seq)
        critic_states = self._apply_compact_context(global_states_seq, compact_context_seq,
                                                    self.critic_context_adapter)
        log_probs, entropy = self.actor.evaluate_actions(actor_observations, initial_hxs,
                                                         actions_seq, masks, agent_skills_seq)
        values, _ = self.critic(critic_states, initial_critic_hxs, masks, team_skills_seq)
        return log_probs, values, entropy


class GASRolloutBuffer(RolloutBuffer):
    """The core rollout buffer with a ``snapshot_width``-wide stored central snapshot state row."""

    def __init__(self, *args, snapshot_width: int, **kwargs):
        self.snapshot_width = int(snapshot_width)   # read by reset(), which __init__ calls
        super().__init__(*args, **kwargs)
        if not self.central_snapshot:
            raise ValueError("GASRolloutBuffer requires central_snapshot=True")

    def reset(self):
        super().reset()
        if self.central_snapshot:
            self.central_snapshot_states = np.zeros(
                (self.num_steps, self.num_envs, self.snapshot_width), dtype=np.float32)

    def add_central_snapshot_batch(self, t, snapshot_states, snapshot_obs):
        """``RolloutBuffer.add_central_snapshot_batch`` with the wide state row; raises on misuse."""
        if t < 0 or t >= self.num_steps:
            raise IndexError(f"central snapshot step index {t} outside [0, {self.num_steps})")
        states = np.asarray(snapshot_states, dtype=np.float32)
        obs = np.asarray(snapshot_obs, dtype=np.float32)
        if states.shape != (self.num_envs, self.snapshot_width):
            raise ValueError(f"central snapshot rows must have shape "
                             f"{(self.num_envs, self.snapshot_width)}, got {states.shape}")
        if obs.shape != (self.num_envs, self.n_agents, self.obs_dim):
            raise ValueError(f"central snapshot observations must have shape "
                             f"{(self.num_envs, self.n_agents, self.obs_dim)}, got {obs.shape}")
        if np.any(self.central_snapshot_mask[t]):
            raise RuntimeError(f"central snapshot step {t} written twice")
        self.central_snapshot_states[t] = states
        self.central_snapshot_obs[t] = obs
        self.central_snapshot_mask[t] = True
        self._cached_rollout_data = None
        return True


def _adam(parameters, *, lr, weight_decay):
    params = list(parameters)
    if len({id(parameter) for parameter in params}) != len(params):
        raise AssertionError("optimizer parameter list contains duplicates")
    return Adam(params, lr=float(lr), weight_decay=float(weight_decay))


def _assert_optimizer_exactly_once(optimizer, parameters, name):
    """Copy of ``agent_count_generalization/models.py::_assert_optimizer_exactly_once``."""
    expected = [id(parameter) for parameter in parameters if parameter.requires_grad]
    actual = [id(parameter) for group in optimizer.param_groups for parameter in group["params"]
              if parameter.requires_grad]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise AssertionError(f"{name} optimizer does not contain each trainable parameter exactly once")


class GASHMASDAgent(HMASDAgent):
    """``HMASDAgent`` with the GAS discoverer, the anchor-carrying snapshot and a decision log.

    Construction (RNG statement): ``HMASDAgent.__init__`` runs unchanged (coordinator first, then
    the base ``SkillDiscoverer``; no discriminator, compact, HA-CTSE or process module exists on
    this configuration), then ``GASSkillDiscoverer(config)`` is drawn from the torch generator
    where the base construction left it and replaces the base discoverer, the two discoverer
    Adam optimizers are rebuilt over ``actor_update_parameters()`` / ``critic_update_parameters()``
    (exactly-once asserted), and the rollout buffer is rebuilt with the same arguments and sampler
    seed and a 332-wide snapshot row (its own ``np.random.default_rng``; no global draw).  The
    coordinator is therefore identical to ``HMASDAgent(config)``'s at the same seed; the base
    discoverer's draws are discarded, so the GAS discoverer and every later torch draw (label and
    action sampling) are shifted relative to a plain agent; numpy and python RNGs are untouched.
    """

    def __init__(self, config, log_dir="logs", device=None, debug=False):
        check_gas_config(config)
        super().__init__(config, log_dir=log_dir, device=device, debug=debug)
        self.decision_log: list[dict] = []
        self.record_decisions = True
        self._gas_env_steps = None
        self._install_gas_modules()

    def _install_gas_modules(self) -> None:
        config = self.config
        if (self.team_discriminator is not None or self.individual_discriminator is not None
                or self.low_level_compact_extractor is not None or self.ha_ctse_editor is not None
                or self.process_encoder is not None or self.native_toy_fixed_primitive_executor
                is not None):
            raise RuntimeError("unexpected optional module on the GAS configuration")
        if not (self.collects_high_level_samples and self.ordinary_completed_segments
                and self.use_central_snapshot and not self.use_discriminator_path):
            raise RuntimeError("GAS agent flags differ from the declared configuration")
        if self.state_norm is not None and getattr(config, "use_statenorm", True):
            raise RuntimeError("state normalizer is active")
        self.skill_discoverer = GASSkillDiscoverer(config, logger=main_logger,
                                                   device=self.device).to(self.device)
        self.discoverer_actor_optimizer = _adam(self.skill_discoverer.actor_update_parameters(),
                                                lr=config.lr_discoverer_actor,
                                                weight_decay=config.weight_decay)
        self.discoverer_critic_optimizer = _adam(self.skill_discoverer.critic_update_parameters(),
                                                 lr=config.lr_discoverer_critic,
                                                 weight_decay=config.weight_decay)
        old = self.rollout_buffer
        sampler_state = old.get_sampler_rng_state()
        self.rollout_buffer = GASRolloutBuffer(
            num_steps=old.num_steps, num_envs=old.num_envs, n_agents=old.n_agents,
            obs_dim=old.obs_dim, action_dim=old.action_dim, gru_hidden_size=old.gru_hidden_size,
            n_Z=old.n_Z, n_z=old.n_z, state_dim=old.state_dim,
            action_space_type=old.action_space_type, compact_dim=0,
            sampler_seed=self.rollout_sampler_seed, d2_enabled=False, central_snapshot=True,
            ordinary_completed_segments=True, snapshot_width=snapshot_width(config))
        if (self.rollout_buffer.get_sampler_rng_state() != sampler_state
                or old.compact_dim != self.rollout_buffer.compact_dim or old.d2_enabled
                or not old.ordinary_completed_segments):
            raise RuntimeError("rebuilt rollout buffer differs from the core one")
        del old
        _assert_optimizer_exactly_once(self.coordinator_optimizer,
                                       self.skill_coordinator.parameters(), "coordinator")
        _assert_optimizer_exactly_once(self.discoverer_actor_optimizer,
                                       self.skill_discoverer.actor_update_parameters(),
                                       "discoverer actor")
        _assert_optimizer_exactly_once(self.discoverer_critic_optimizer,
                                       self.skill_discoverer.critic_update_parameters(),
                                       "discoverer critic")
        width = int(self.skill_discoverer.central_input_dim) + int(config.obs_dim)
        if width != actor_input_width(config):
            raise RuntimeError(f"GAS actor input width {width} != {actor_input_width(config)}")

    # -- snapshot with anchors and labels --------------------------------------------------------
    def _ensure_central_snapshot_arrays(self, num_envs):
        """``HMASDAgent._ensure_central_snapshot_arrays`` with the 332-wide state row."""
        required = int(max(num_envs, 1))
        if self._central_snapshot_states is not None and self._central_snapshot_capacity >= required:
            return
        old_capacity = self._central_snapshot_capacity
        new_capacity = max(required, old_capacity * 2 if old_capacity else required)
        states = np.zeros((new_capacity, snapshot_width(self.config)), dtype=np.float64)
        observations = np.zeros((new_capacity, self.config.n_agents, self.config.obs_dim),
                                dtype=np.float32)
        valid = np.zeros(new_capacity, dtype=np.bool_)
        if old_capacity > 0:
            states[:old_capacity] = self._central_snapshot_states[:old_capacity]
            observations[:old_capacity] = self._central_snapshot_obs[:old_capacity]
            valid[:old_capacity] = self._central_snapshot_valid[:old_capacity]
        self._central_snapshot_states = states
        self._central_snapshot_obs = observations
        self._central_snapshot_valid = valid
        self._central_snapshot_capacity = new_capacity

    def step(self, states_batch, observations_batch, env_steps_batch, dones_batch,
             deterministic=False, return_step_data=False, build_infos=True):
        """``HMASDAgent.step``; the episode steps are kept for the decision log only."""
        self._gas_env_steps = np.asarray(env_steps_batch, dtype=np.int64).copy()
        try:
            return super().step(states_batch, observations_batch, env_steps_batch, dones_batch,
                                deterministic=deterministic, return_step_data=return_step_data,
                                build_infos=build_infos)
        finally:
            self._gas_env_steps = None

    def _refresh_central_snapshots(self, states_batch, observations_batch, refresh_mask):
        """Refresh the decided lanes: state | anchors(state) | the labels just decoded."""
        refresh_mask = np.asarray(refresh_mask, dtype=np.bool_)
        self._ensure_central_snapshot_arrays(int(refresh_mask.shape[0]))
        indices = np.flatnonzero(refresh_mask)
        if not indices.size:
            return
        states = np.asarray(states_batch, dtype=np.float64)
        observations = np.asarray(observations_batch, dtype=np.float32)
        state_end = int(self.config.state_dim)
        anchors_end = state_end + ANCHOR_DIM
        n_agents = int(self.config.n_agents)
        for lane in (int(index) for index in indices):
            if int(self.env_timers.get(lane, -1)) != 0:
                raise RuntimeError(f"GAS snapshot refresh on lane {lane} without a team decision "
                                   "at this step")
            labels = np.asarray(self.env_agent_skills[lane], dtype=np.int64).reshape(-1)
            if labels.shape != (n_agents,) or labels.min() < 0 or labels.max() >= N_LABELS:
                raise RuntimeError(f"invalid labels {labels.tolist()} on lane {lane}")
            anchors = anchors_from_state(states[lane])
            row = self._central_snapshot_states[lane]
            row[:state_end] = states[lane]
            row[state_end:anchors_end] = anchors.reshape(-1)
            row[anchors_end:] = labels
            self._central_snapshot_obs[lane] = observations[lane]
            self._central_snapshot_valid[lane] = True
            if self.record_decisions:
                steps = self._gas_env_steps
                self.decision_log.append({
                    "env": lane, "step": None if steps is None else int(steps[lane]),
                    "labels": labels.tolist(), "anchors": anchors.tolist(),
                    "own_xy": observations[lane][:, 0:2].astype(np.float64).tolist()})

    def pop_decision_log(self) -> list[dict]:
        rows, self.decision_log = self.decision_log, []
        return rows

    def _central_actor_input(self, env_indices, n_agents):
        """(len(env_indices) * n_agents, 3253), env-major and agent-minor, from the held rows."""
        env_indices = np.asarray(env_indices, dtype=np.int64).reshape(-1)
        if not self._central_snapshot_valid[env_indices].all():
            raise RuntimeError("GAS central snapshot is missing for an active lane")
        count = env_indices.size
        state_end = int(self.config.state_dim)
        anchors_end = state_end + ANCHOR_DIM
        held = self._central_snapshot_states[env_indices]
        states = self._normalize_states(held[:, :state_end], update=False)
        observations = self._normalize_observations(
            self._central_snapshot_obs[env_indices][:, :n_agents], update=False)
        per_env = np.concatenate([np.asarray(states, dtype=np.float32).reshape(count, -1),
                                  held[:, state_end:anchors_end].astype(np.float32)], axis=1)
        own_label = held[:, anchors_end:anchors_end + n_agents].astype(np.float32).reshape(-1, 1)
        joint = np.asarray(observations, dtype=np.float32).reshape(count, -1)
        ego = np.tile(np.eye(n_agents, dtype=np.float32), (count, 1))
        return np.concatenate([np.repeat(per_env, n_agents, axis=0), own_label,
                               np.repeat(joint, n_agents, axis=0), ego], axis=1)

    def _central_actor_input_from_replay(self, central_states_seq, central_obs_seq, ego_indices):
        """The same layout from stored rows: (T, B, 332), (T, B, A, obs_dim), (B,)."""
        time_steps, batch = central_states_seq.shape[:2]
        n_agents = central_obs_seq.shape[2]
        if central_states_seq.shape[-1] != snapshot_width(self.config):
            raise ValueError(f"stored GAS snapshot rows must be {snapshot_width(self.config)} wide")
        state_end = int(self.config.state_dim)
        anchors_end = state_end + ANCHOR_DIM
        ego_long = ego_indices.long().to(central_states_seq.device)
        labels = central_states_seq[..., anchors_end:anchors_end + n_agents]
        own_label = torch.gather(labels, -1,
                                 ego_long.view(1, batch, 1).expand(time_steps, batch, 1))
        ego = F.one_hot(ego_long, num_classes=n_agents).to(dtype=central_states_seq.dtype)
        ego = ego.unsqueeze(0).expand(time_steps, batch, n_agents)
        return torch.cat([central_states_seq[..., :anchors_end], own_label,
                          central_obs_seq.reshape(time_steps, batch, -1), ego], dim=-1)


def build_agent(config, log_dir, device):
    """``GASHMASDAgent(config)`` (the caller seeds first, as ``b02/training.py::_seeded_agent``)."""
    return GASHMASDAgent(config, log_dir=str(log_dir), device=device)
