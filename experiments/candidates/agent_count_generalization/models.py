"""Count-stable model substitutions on the existing HMASD update paths."""

from __future__ import annotations

import copy

import torch
from torch import nn
from torch.optim import Adam

from hmasd.agent import HMASDAgent
from hmasd.networks import initialize_weights

from .adapter import MAX_UAVS, N_USERS, STATE_DIM


class StateSetEncoder(nn.Module):
    """Encode the padded S1 state without learning UAV slot identities."""

    def __init__(self, output_dim: int, *, hidden_dim: int = 256, uav_hidden_dim: int = 64):
        super().__init__()
        self.output_dim = int(output_dim)
        self.uav_encoder = nn.Sequential(
            nn.Linear(3, int(uav_hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(uav_hidden_dim), int(uav_hidden_dim)),
            nn.Tanh(),
        )
        pooled_dim = 2 * int(uav_hidden_dim) + 1 + 2 * N_USERS + 1
        if int(uav_hidden_dim) == 64 and pooled_dim != 230:
            raise AssertionError("unexpected state-set pooled width")
        self.output = nn.Sequential(
            nn.Linear(pooled_dim, int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), self.output_dim),
            nn.Tanh(),
        )

    def forward(self, state):
        if state.shape[-1] != STATE_DIM:
            raise ValueError(f"state must have width {STATE_DIM}, got {tuple(state.shape)}")
        original_shape = state.shape[:-1]
        flat = state.float().reshape(-1, STATE_DIM)
        uavs = flat[:, : MAX_UAVS * 3].reshape(-1, MAX_UAVS, 3)
        valid = flat[:, MAX_UAVS * 3 : MAX_UAVS * 4]
        users = flat[:, MAX_UAVS * 4 : MAX_UAVS * 4 + 2 * N_USERS]
        time = flat[:, -1:]

        if bool(((valid != 0.0) & (valid != 1.0)).any()):
            raise ValueError("UAV validity entries must be binary")
        counts = valid.sum(dim=-1, keepdim=True)
        if bool((counts <= 0.0).any()):
            raise ValueError("state must contain at least one valid UAV")
        encoded = self.uav_encoder(uavs)
        weights = valid.unsqueeze(-1)
        mean = (encoded * weights).sum(dim=1) / counts
        masked = encoded.masked_fill(~valid.bool().unsqueeze(-1), float("-inf"))
        maximum = masked.max(dim=1).values
        pooled = torch.cat([mean, maximum, counts / float(MAX_UAVS), users, time], dim=-1)
        return self.output(pooled).reshape(*original_shape, self.output_dim)


class SharedValueHeads(nn.Module):
    """Index-compatible access to one registered per-agent value head."""

    def __init__(self, input_dim: int, n_agents: int):
        super().__init__()
        self.head = nn.Linear(int(input_dim), 1)
        initialize_weights(self.head, gain=0.01)
        self.n_agents = int(n_agents)

    def __getitem__(self, index):
        if not 0 <= int(index) < self.n_agents:
            raise IndexError(index)
        return self.head

    def __len__(self):
        return self.n_agents

    def forward(self, features):
        return self.head(features)


class SetActorBase(nn.Module):
    """SET actor preprocessor for the core held-snapshot input layout."""

    def __init__(self, config):
        super().__init__()
        self.obs_dim = int(config.obs_dim)
        self.state_dim = int(config.state_dim)
        self.n_agents = int(config.n_agents)
        self.hidden_size = int(config.hidden_size)
        if self.state_dim != STATE_DIM:
            raise ValueError(f"SET requires state_dim={STATE_DIM}")
        if self.obs_dim != 104:
            raise ValueError(f"SET requires native S1 obs_dim=104, got {self.obs_dim}")

        # Actual experiment widths are 128/256/256.  Tiny technical configs can
        # reduce them by reducing hidden_size, without changing the input contract.
        row_width = min(128, self.hidden_size)
        feature_width = min(256, self.hidden_size)
        fusion_width = min(256, self.hidden_size)
        self.row_encoder = nn.Sequential(
            nn.Linear(self.obs_dim, row_width),
            nn.Tanh(),
            nn.Linear(row_width, row_width),
            nn.Tanh(),
        )
        self.state_encoder = StateSetEncoder(
            feature_width,
            hidden_dim=feature_width,
            uav_hidden_dim=min(64, self.hidden_size),
        )
        self.concat_dim = 2 * row_width + 1 + 2 * self.obs_dim + feature_width
        if self.hidden_size == 256 and self.concat_dim != 721:
            raise AssertionError(f"actual SET concatenation width is {self.concat_dim}, expected 721")
        self.fusion = nn.Sequential(
            nn.Linear(self.concat_dim, fusion_width),
            nn.Tanh(),
            nn.Linear(fusion_width, self.hidden_size),
            nn.Tanh(),
        )

    @property
    def input_dim(self):
        return self.obs_dim + self.state_dim + self.n_agents * self.obs_dim + self.n_agents

    def forward(self, actor_input):
        if actor_input.shape[-1] != self.input_dim:
            raise ValueError(
                f"SET actor input must have width {self.input_dim}, got {tuple(actor_input.shape)}"
            )
        tensor = actor_input.float()
        current = tensor[..., : self.obs_dim]
        start = self.obs_dim
        state = tensor[..., start : start + self.state_dim]
        start += self.state_dim
        held = tensor[..., start : start + self.n_agents * self.obs_dim].reshape(
            *tensor.shape[:-1], self.n_agents, self.obs_dim
        )
        start += self.n_agents * self.obs_dim
        ego = tensor[..., start : start + self.n_agents]
        if bool((ego.sum(dim=-1) - 1.0).abs().gt(1e-5).any()) or bool(
            ((ego < -1e-6) | (ego > 1.0 + 1e-6)).any()
        ):
            raise ValueError("held ego selector must be one-hot")

        rows = self.row_encoder(held)
        row_mean = rows.mean(dim=-2)
        row_max = rows.max(dim=-2).values
        held_ego = (held * ego.unsqueeze(-1)).sum(dim=-2)
        count = tensor.new_full((*tensor.shape[:-1], 1), self.n_agents / float(MAX_UAVS))
        features = torch.cat(
            [row_mean, row_max, count, held_ego, current, self.state_encoder(state)], dim=-1
        )
        return self.fusion(features)


class _EncodedTeamDiscriminator(nn.Module):
    """Feed a count-stable state feature into the unchanged H6 classifier."""

    def __init__(self, classifier: nn.Module, config):
        super().__init__()
        self.state_encoder = StateSetEncoder(
            int(config.state_dim),
            hidden_dim=min(256, int(config.hidden_size)),
            uav_hidden_dim=min(64, int(config.hidden_size)),
        )
        self.classifier = classifier

    def forward(self, state, age=None):
        return self.classifier(self.state_encoder(state), age=age)


def _adam(parameters, *, lr, weight_decay):
    params = list(parameters)
    if len({id(parameter) for parameter in params}) != len(params):
        raise AssertionError("optimizer parameter list contains duplicates")
    return Adam(params, lr=float(lr), weight_decay=float(weight_decay))


def _assert_optimizer_exactly_once(optimizer, parameters, name):
    expected = [id(parameter) for parameter in parameters if parameter.requires_grad]
    actual = [
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
        if parameter.requires_grad
    ]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise AssertionError(f"{name} optimizer does not contain each trainable parameter exactly once")


def build_agent(config, log_dir):
    """Construct a core agent, substitute count-stable modules, and rebuild affected Adam state."""
    arm = str(getattr(config, "count_arm", "")).upper()
    if arm not in {"H6", "SET"}:
        raise ValueError("config.count_arm must be H6 or SET")
    if str(getattr(config, "policy_interruption_mode", "off")) != "off":
        raise ValueError("count comparison requires ordinary fixed-clock mode")
    if bool(getattr(config, "use_horizon_window", False)) or int(config.k) != 10:
        raise ValueError("count comparison requires the fixed ten-step clock")
    if bool(getattr(config, "use_lr_decay", False)):
        raise ValueError("count comparison does not support an LR schedule")
    if int(config.state_dim) != STATE_DIM or int(config.obs_dim) != 104:
        raise ValueError("unexpected count-transfer state/observation contract")
    if bool(getattr(config, "use_central_snapshot_in_flat_actor", False)) != (arm == "SET"):
        raise ValueError("central snapshot must be enabled for SET and disabled for H6")

    agent = HMASDAgent(config, log_dir=log_dir, device=torch.device("cpu"))
    device = agent.device

    agent.skill_coordinator.state_embedding = StateSetEncoder(
        int(config.embedding_dim),
        hidden_dim=min(256, int(config.hidden_size)),
        uav_hidden_dim=min(64, int(config.hidden_size)),
    ).to(device)
    agent.skill_coordinator.value_heads_obs = SharedValueHeads(
        int(config.embedding_dim), int(config.n_agents)
    ).to(device)
    agent.skill_discoverer.critic.base = StateSetEncoder(
        int(config.hidden_size),
        hidden_dim=min(256, int(config.hidden_size)),
        uav_hidden_dim=min(64, int(config.hidden_size)),
    ).to(device)

    agent.coordinator_optimizer = _adam(
        agent.skill_coordinator.parameters(),
        lr=config.lr_coordinator,
        weight_decay=config.weight_decay,
    )
    agent.discoverer_critic_optimizer = _adam(
        agent.skill_discoverer.critic_update_parameters(),
        lr=config.lr_discoverer_critic,
        weight_decay=config.weight_decay,
    )

    if arm == "SET":
        agent.skill_discoverer.actor.base = SetActorBase(config).to(device)
        agent.discoverer_actor_optimizer = _adam(
            agent.skill_discoverer.actor_update_parameters(),
            lr=config.lr_discoverer_actor,
            weight_decay=config.weight_decay,
        )
    elif agent.team_discriminator is not None:
        agent.team_discriminator = _EncodedTeamDiscriminator(
            agent.team_discriminator, config
        ).to(device)
        agent.team_discriminator_optimizer = _adam(
            agent.team_discriminator.parameters(),
            lr=config.lr_discriminator,
            weight_decay=config.weight_decay,
        )

    _assert_optimizer_exactly_once(
        agent.coordinator_optimizer, agent.skill_coordinator.parameters(), "coordinator"
    )
    _assert_optimizer_exactly_once(
        agent.discoverer_critic_optimizer,
        agent.skill_discoverer.critic_update_parameters(),
        "discoverer critic",
    )
    if arm == "SET":
        _assert_optimizer_exactly_once(
            agent.discoverer_actor_optimizer,
            agent.skill_discoverer.actor_update_parameters(),
            "discoverer actor",
        )
    if agent.team_discriminator is not None:
        _assert_optimizer_exactly_once(
            agent.team_discriminator_optimizer,
            agent.team_discriminator.parameters(),
            "team discriminator",
        )
    return agent


def _strict_copy_module(target, source, name):
    target_state = target.state_dict()
    source_state = source.state_dict()
    if target_state.keys() != source_state.keys():
        raise ValueError(f"{name} state keys differ across runtimes")
    mismatched = {
        key: (tuple(target_state[key].shape), tuple(source_state[key].shape))
        for key in target_state
        if target_state[key].shape != source_state[key].shape
    }
    if mismatched:
        raise ValueError(f"{name} state shapes differ across runtimes: {mismatched}")
    target.load_state_dict(source_state, strict=True)


def strict_sync(target, source):
    """Strictly transfer learned state to an evaluation runtime at another N."""
    _strict_copy_module(target.skill_coordinator, source.skill_coordinator, "coordinator")
    _strict_copy_module(target.skill_discoverer, source.skill_discoverer, "discoverer")
    for attribute in ("team_discriminator", "individual_discriminator"):
        target_module = getattr(target, attribute, None)
        source_module = getattr(source, attribute, None)
        if (target_module is None) != (source_module is None):
            raise ValueError(f"{attribute} presence differs across runtimes")
        if target_module is not None:
            _strict_copy_module(target_module, source_module, attribute)

    for attribute in (
        "obs_norm",
        "state_norm",
        "value_norm_coordinator",
        "value_norm_discoverer",
    ):
        setattr(target, attribute, copy.deepcopy(getattr(source, attribute, None)))
    target.train(False)
    for lane in range(int(getattr(target.config, "num_envs", 1))):
        target.reset_env_state(lane)
    return target
