"""Agent factory for the macro-step contracts (coupled_host_joint_skills_stage1, T-W).

``models.build_agent`` stays the b01 factory (it asserts the 133/90 widths and the ten-step
caps).  ``build_macro_agent`` applies the same substitutions (count-stable state encoders for the
coordinator, the discoverer critic and the team discriminator; the SET actor preprocessor; Adam
rebuilt for the substituted modules; d2 theta_0 recaptured) with two declared differences:

* the clock is ``k = 1`` in macro units (one macro step = 10 host steps); arm H runs d2 with
  ``skill_cap_k_max = team_cap_k_Z = 1`` (a team decision every macro step), SET the ``off``
  route with its central snapshot refreshed every macro step;
* when the observation and state carry the 36-float planner menu (slot contract), the encoders
  are width-parametric: ``MenuStateSetEncoder`` appends the menu block to the pooled state
  features and ``MenuSetActorBase`` is ``SetActorBase`` at the wider observation/state widths.
  Without a menu (target/offset contracts) the b01 classes are used unchanged.

The action head comes from the core (``R_Actor``): ``Discrete(6)`` for slot
(``config.action_space_type = "discrete"``), a 3-D diagonal Gaussian for target/offset (raw
samples; the adapter squashes them).
"""

from __future__ import annotations

import math

import torch
from torch import nn

from hmasd.agent import HMASDAgent

from .adapter import MAX_UAVS, N_USERS, OBS_DIM, STATE_DIM
from .models import (
    ARMS,
    SetActorBase,
    SharedValueHeads,
    StateSetEncoder,
    _adam,
    _assert_optimizer_exactly_once,
    route_facts,
)

MACRO_K_UNITS = 1
ENCODER_CLASS_NAMES = frozenset({"StateSetEncoder", "SetActorBase", "MenuStateSetEncoder",
                                 "MenuSetActorBase"})


class MenuStateSetEncoder(nn.Module):
    """``StateSetEncoder`` over ``[133-dim state | extra block]``; the block joins the pooled features."""

    def __init__(self, output_dim: int, *, extra_dim: int, hidden_dim: int = 256,
                 uav_hidden_dim: int = 64):
        super().__init__()
        if int(extra_dim) <= 0:
            raise ValueError("MenuStateSetEncoder needs a positive extra width; use StateSetEncoder")
        self.output_dim = int(output_dim)
        self.extra_dim = int(extra_dim)
        self.state_dim = STATE_DIM + self.extra_dim
        self.uav_encoder = nn.Sequential(
            nn.Linear(3, int(uav_hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(uav_hidden_dim), int(uav_hidden_dim)),
            nn.Tanh(),
        )
        pooled_dim = 2 * int(uav_hidden_dim) + 1 + 2 * N_USERS + 1 + self.extra_dim
        self.output = nn.Sequential(
            nn.Linear(pooled_dim, int(hidden_dim)),
            nn.Tanh(),
            nn.Linear(int(hidden_dim), self.output_dim),
            nn.Tanh(),
        )

    def forward(self, state):
        if state.shape[-1] != self.state_dim:
            raise ValueError(f"state must have width {self.state_dim}, got {tuple(state.shape)}")
        original_shape = state.shape[:-1]
        flat = state.float().reshape(-1, self.state_dim)
        uavs = flat[:, : MAX_UAVS * 3].reshape(-1, MAX_UAVS, 3)
        valid = flat[:, MAX_UAVS * 3 : MAX_UAVS * 4]
        users = flat[:, MAX_UAVS * 4 : MAX_UAVS * 4 + 2 * N_USERS]
        time = flat[:, STATE_DIM - 1 : STATE_DIM]
        extra = flat[:, STATE_DIM:]
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
        pooled = torch.cat([mean, maximum, counts / float(MAX_UAVS), users, time, extra], dim=-1)
        return self.output(pooled).reshape(*original_shape, self.output_dim)


def _state_encoder(output_dim, config):
    extra = int(config.state_dim) - STATE_DIM
    kwargs = dict(hidden_dim=min(256, int(config.hidden_size)),
                  uav_hidden_dim=min(64, int(config.hidden_size)))
    if extra == 0:
        return StateSetEncoder(int(output_dim), **kwargs)
    return MenuStateSetEncoder(int(output_dim), extra_dim=extra, **kwargs)


class MenuSetActorBase(nn.Module):
    """``SetActorBase`` at observation width ``90 + m`` and state width ``133 + m`` (menu width m)."""

    def __init__(self, config):
        super().__init__()
        self.obs_dim = int(config.obs_dim)
        self.state_dim = int(config.state_dim)
        self.n_agents = int(config.n_agents)
        self.hidden_size = int(config.hidden_size)
        extra = self.state_dim - STATE_DIM
        if extra <= 0 or self.obs_dim - OBS_DIM != extra:
            raise ValueError("MenuSetActorBase needs equal positive menu widths on obs and state")
        row_width = min(128, self.hidden_size)
        feature_width = min(256, self.hidden_size)
        fusion_width = min(256, self.hidden_size)
        self.row_encoder = nn.Sequential(
            nn.Linear(self.obs_dim, row_width),
            nn.Tanh(),
            nn.Linear(row_width, row_width),
            nn.Tanh(),
        )
        self.state_encoder = MenuStateSetEncoder(
            feature_width, extra_dim=extra, hidden_dim=feature_width,
            uav_hidden_dim=min(64, self.hidden_size),
        )
        self.concat_dim = 2 * row_width + 1 + 2 * self.obs_dim + feature_width
        self.fusion = nn.Sequential(
            nn.Linear(self.concat_dim, fusion_width),
            nn.Tanh(),
            nn.Linear(fusion_width, self.hidden_size),
            nn.Tanh(),
        )

    @property
    def input_dim(self):
        return self.obs_dim + self.state_dim + self.n_agents * self.obs_dim + self.n_agents

    forward = SetActorBase.forward


class _MenuEncodedTeamDiscriminator(nn.Module):
    """``models._EncodedTeamDiscriminator`` with a width-parametric state encoder."""

    def __init__(self, classifier: nn.Module, config):
        super().__init__()
        self.state_encoder = _state_encoder(int(config.state_dim), config)
        self.classifier = classifier

    def forward(self, state, age=None):
        return self.classifier(self.state_encoder(state), age=age)


def assert_macro_route(agent, arm):
    facts = route_facts(agent)
    k = MACRO_K_UNITS
    if arm == "H":
        expected = {"policy_interruption_mode": "d2", "d2_enabled": True, "d2_k_max": k, "d2_k_Z": k,
                    "d2_age_feature": "off", "use_ha_ctse": False, "use_central_snapshot": False}
        infinite = math.isinf(facts["d2_cost_c"]) and facts["d2_cost_c"] > 0 and \
            math.isinf(facts["d2_cost_c_Z"]) and facts["d2_cost_c_Z"] > 0
    else:
        expected = {"policy_interruption_mode": "off", "d2_enabled": False, "d2_k_max": k, "d2_k_Z": k,
                    "d2_age_feature": "off", "use_ha_ctse": False, "use_central_snapshot": True}
        infinite = True
    wrong = {key: facts[key] for key, value in expected.items() if facts[key] != value}
    if wrong or not infinite:
        raise AssertionError(f"macro arm {arm} built on the wrong route: {wrong or facts}")
    return facts


def build_macro_agent(config, log_dir):
    """Macro-contract counterpart of ``models.build_agent`` (see the module doc)."""
    arm = str(getattr(config, "contract_arm", ""))
    if arm not in ARMS:
        raise ValueError("config.contract_arm must be H or SET")
    contract = str(getattr(config, "macro_contract", ""))
    if contract not in ("target", "slot", "offset"):
        raise ValueError("config.macro_contract must be target, slot or offset")
    mode = str(getattr(config, "policy_interruption_mode", "off"))
    k = MACRO_K_UNITS
    if arm == "H":
        if mode != "d2":
            raise ValueError("macro arm H runs the D-route (policy_interruption_mode='d2')")
        if int(getattr(config, "skill_cap_k_max", -1)) != k or getattr(config, "team_cap_k_Z", None) != k:
            raise ValueError("macro arm H requires skill_cap_k_max = team_cap_k_Z = 1 (macro units)")
        if not (math.isinf(float(config.interruption_cost_c)) and float(config.interruption_cost_c) > 0
                and math.isinf(float(config.interruption_cost_c_Z)) and float(config.interruption_cost_c_Z) > 0):
            raise ValueError("macro arm H requires both interruption costs = +inf")
        if str(getattr(config, "age_feature", "off")) != "off":
            raise ValueError("macro arm H requires the age feature off")
    elif mode != "off":
        raise ValueError("macro arm SET runs the native 'off' route")
    if bool(getattr(config, "use_horizon_window", False)) or int(config.k) != k:
        raise ValueError("macro fits require HA-CTSE off and k = 1 in macro units")
    if bool(getattr(config, "use_lr_decay", False)):
        raise ValueError("macro fits do not support an LR schedule")
    discrete = str(getattr(config, "action_space_type", "continuous")) == "discrete"
    if discrete != (contract == "slot"):
        raise ValueError("the slot contract is discrete; target/offset are continuous")
    if (int(config.action_dim) != 6) if discrete else (int(config.action_dim) != 3):
        raise ValueError("unexpected macro action width")
    extra = int(config.state_dim) - STATE_DIM
    if extra < 0 or int(config.obs_dim) - OBS_DIM != extra:
        raise ValueError("macro obs/state must extend the b01 widths by the same menu block")
    if bool(getattr(config, "use_central_snapshot_in_flat_actor", False)) != (arm == "SET"):
        raise ValueError("central snapshot must be enabled for SET and disabled for H")

    agent = HMASDAgent(config, log_dir=log_dir, device=torch.device("cpu"))
    device = agent.device
    agent.skill_coordinator.state_embedding = _state_encoder(int(config.embedding_dim), config).to(device)
    agent.skill_coordinator.value_heads_obs = SharedValueHeads(
        int(config.embedding_dim), int(config.n_agents)
    ).to(device)
    agent.skill_discoverer.critic.base = _state_encoder(int(config.hidden_size), config).to(device)
    agent.coordinator_optimizer = _adam(agent.skill_coordinator.parameters(),
                                        lr=config.lr_coordinator, weight_decay=config.weight_decay)
    agent.discoverer_critic_optimizer = _adam(agent.skill_discoverer.critic_update_parameters(),
                                              lr=config.lr_discoverer_critic,
                                              weight_decay=config.weight_decay)
    if arm == "SET":
        base = SetActorBase(config) if extra == 0 else MenuSetActorBase(config)
        agent.skill_discoverer.actor.base = base.to(device)
        agent.discoverer_actor_optimizer = _adam(agent.skill_discoverer.actor_update_parameters(),
                                                 lr=config.lr_discoverer_actor,
                                                 weight_decay=config.weight_decay)
    elif agent.team_discriminator is not None:
        agent.team_discriminator = _MenuEncodedTeamDiscriminator(agent.team_discriminator, config).to(device)
        agent.team_discriminator_optimizer = _adam(agent.team_discriminator.parameters(),
                                                   lr=config.lr_discriminator,
                                                   weight_decay=config.weight_decay)
    if arm == "H":
        with torch.no_grad():
            agent.d2_coordinator_theta0 = [p.detach().clone() for p in agent.skill_coordinator.parameters()]
            agent.d2_coordinator_theta0_norm = float(
                torch.sqrt(sum((p.double() ** 2).sum() for p in agent.d2_coordinator_theta0)).item())
    assert_macro_route(agent, arm)
    _assert_optimizer_exactly_once(agent.coordinator_optimizer, agent.skill_coordinator.parameters(),
                                   "coordinator")
    _assert_optimizer_exactly_once(agent.discoverer_critic_optimizer,
                                   agent.skill_discoverer.critic_update_parameters(), "discoverer critic")
    if arm == "SET":
        _assert_optimizer_exactly_once(agent.discoverer_actor_optimizer,
                                       agent.skill_discoverer.actor_update_parameters(), "discoverer actor")
    if agent.team_discriminator is not None:
        _assert_optimizer_exactly_once(agent.team_discriminator_optimizer,
                                       agent.team_discriminator.parameters(), "team discriminator")
    return agent
