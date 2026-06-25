from dataclasses import dataclass
from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

from hmasd.networks import OPT, initialize_weights


@dataclass
class HACTSEOutput:
    compact: torch.Tensor
    team_code: torch.Tensor
    team_vector: torch.Tensor
    log_prob_team_code: torch.Tensor
    entropy_team_code: torch.Tensor
    active_skill_prev: torch.Tensor
    active_skill: torch.Tensor
    candidate_skill: torch.Tensor
    skill_age_prev: torch.Tensor
    skill_age: torch.Tensor
    requested_edit_mask: torch.Tensor
    executed_edit_mask: torch.Tensor
    log_prob_term: torch.Tensor
    log_prob_skill: torch.Tensor
    duration_candidate: torch.Tensor
    duration_target: torch.Tensor
    duration_remaining: torch.Tensor
    log_prob_duration: torch.Tensor
    entropy_term: torch.Tensor
    entropy_skill: torch.Tensor
    entropy_duration: torch.Tensor
    initial_assignment_mask: torch.Tensor
    state_values: torch.Tensor
    agent_values: torch.Tensor
    cd_loss: torch.Tensor
    cmi_loss: torch.Tensor
    aggregation_entropy: torch.Tensor
    h_min_mask: torch.Tensor
    h_max_force_mask: torch.Tensor
    term_logits: torch.Tensor
    skill_logits: torch.Tensor
    duration_logits: torch.Tensor

    def as_dict(self) -> Dict[str, torch.Tensor]:
        return self.__dict__.copy()


class OPTCompactExtractor(nn.Module):
    """Builds OPT interaction compact c_tau without treating it as a skill."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.state_dim = int(config.state_dim)
        self.obs_dim = int(config.obs_dim)
        self.compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 128)))
        self.num_prototypes = int(getattr(config, "opt_num_prototypes", 4))
        self.use_opt = bool(getattr(config, "use_opt_compact", True))

        self.state_embedding = nn.Linear(self.state_dim, self.compact_dim)
        self.obs_embedding = nn.Linear(self.obs_dim, self.compact_dim)

        if self.use_opt:
            self.opt = OPT(
                input_dim=self.compact_dim,
                num_prototypes=self.num_prototypes,
                prototype_dim=self.compact_dim,
                num_layers=int(getattr(config, "opt_layers", 1)),
            )
            self.compact_projection = nn.Linear(self.compact_dim, self.compact_dim)
        else:
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=self.compact_dim,
                nhead=max(1, int(getattr(config, "n_heads", 1))),
                dim_feedforward=self.compact_dim * 4,
                batch_first=True,
            )
            self.encoder = nn.TransformerEncoder(
                encoder_layer,
                num_layers=max(1, int(getattr(config, "n_encoder_layers", 1))),
            )
            self.compact_projection = nn.Linear(self.compact_dim, self.compact_dim)

        self._init_weights()

    def _init_weights(self):
        initialize_weights(self.state_embedding)
        initialize_weights(self.obs_embedding)
        initialize_weights(self.compact_projection)

    def forward(self, state, observations):
        batch_size, n_agents, obs_dim = observations.shape
        state = state.float()
        observations = observations.float()

        embedded_state = self.state_embedding(state).unsqueeze(1)
        embedded_obs = self.obs_embedding(observations.reshape(-1, obs_dim)).reshape(
            batch_size, n_agents, self.compact_dim
        )
        entity_sequence = torch.cat([embedded_state, embedded_obs], dim=1)

        if self.use_opt:
            opt_output, cd_loss, cmi_loss, aggregation_weights = self.opt(entity_sequence)
            encoded = opt_output
            if not bool(getattr(self.config, "opt_use_cd_loss", True)):
                cd_loss = torch.zeros((), device=state.device, requires_grad=True)
            if bool(getattr(self.config, "opt_use_cmi_loss", False)):
                avg_weights = aggregation_weights.mean(dim=0).clamp_min(1e-8)
                uniform = torch.full_like(avg_weights, 1.0 / max(1, self.num_prototypes))
                usage_balance_loss = F.kl_div(avg_weights.log(), uniform, reduction="sum")
                cmi_loss = cmi_loss + usage_balance_loss
            else:
                cmi_loss = torch.zeros((), device=state.device, requires_grad=True)
        else:
            encoded = self.encoder(entity_sequence)
            cd_loss = torch.zeros((), device=state.device, requires_grad=True)
            cmi_loss = torch.zeros((), device=state.device, requires_grad=True)
            aggregation_weights = torch.full(
                (batch_size, self.num_prototypes),
                1.0 / max(1, self.num_prototypes),
                device=state.device,
            )

        compact = self.compact_projection(encoded.mean(dim=1))
        aggregation_entropy = -(
            aggregation_weights * torch.log(aggregation_weights.clamp_min(1e-8))
        ).sum(dim=-1)

        return compact, cd_loss, cmi_loss, aggregation_weights, aggregation_entropy


class CompactTeamBridge(nn.Module):
    """Maps interaction compact c_tau to team coordination code g_tau."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.bridge_type = str(getattr(config, "team_bridge_type", "deterministic"))
        self.compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 128)))
        self.team_code_dim = int(getattr(config, "team_code_dim", getattr(config, "embedding_dim", 128)))
        self.num_team_codes = int(getattr(config, "num_team_codes", getattr(config, "n_Z", 1)))

        self.vector_bridge = nn.Sequential(
            nn.Linear(self.compact_dim, self.team_code_dim),
            nn.LayerNorm(self.team_code_dim),
            nn.GELU(),
        )
        self.code_head = nn.Linear(self.team_code_dim, self.num_team_codes)
        self.code_embedding = nn.Embedding(self.num_team_codes, self.team_code_dim)
        self._init_weights()

    def _init_weights(self):
        for module in self.vector_bridge:
            if isinstance(module, nn.Linear):
                initialize_weights(module)
        initialize_weights(self.code_head, last_layer_gain=0.01)
        initialize_weights(self.code_embedding)

    def forward(self, compact, deterministic=False, forced_team_code: Optional[torch.Tensor] = None):
        batch_size = compact.shape[0]
        device = compact.device

        if self.bridge_type == "none":
            team_code = torch.zeros(batch_size, dtype=torch.long, device=device)
            team_vector = torch.zeros(batch_size, self.team_code_dim, device=device)
            zeros = torch.zeros(batch_size, device=device)
            return team_code, team_vector, zeros, zeros, torch.zeros(batch_size, self.num_team_codes, device=device)

        base_vector = self.vector_bridge(compact)
        logits = torch.clamp(self.code_head(base_vector), -50.0, 50.0)

        if self.bridge_type == "stochastic":
            dist = Categorical(logits=logits)
            if forced_team_code is not None:
                team_code = forced_team_code.long()
            elif deterministic:
                team_code = logits.argmax(dim=-1)
            else:
                team_code = dist.sample()
            team_vector = self.code_embedding(team_code)
            log_prob = dist.log_prob(team_code)
            entropy = dist.entropy()
            return team_code, team_vector, log_prob, entropy, logits

        team_code = logits.argmax(dim=-1) if forced_team_code is None else forced_team_code.long()
        zeros = torch.zeros(batch_size, device=device)
        return team_code, base_vector, zeros, zeros, logits


class CompactTeamDiscriminator(nn.Module):
    """Team-code discriminator q_G(g | s, c_tau) for HA-CTSE."""

    def __init__(self, config):
        super().__init__()
        self.state_dim = int(config.state_dim)
        self.compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 128)))
        self.hidden_size = int(getattr(config, "hidden_size", 128))
        self.num_team_codes = int(getattr(config, "num_team_codes", getattr(config, "n_Z", 1)))
        self.state_encoder = nn.Sequential(
            nn.LayerNorm(self.state_dim),
            nn.Linear(self.state_dim, self.hidden_size),
            nn.GELU(),
        )
        self.compact_encoder = nn.Sequential(
            nn.LayerNorm(self.compact_dim),
            nn.Linear(self.compact_dim, self.hidden_size),
            nn.GELU(),
        )
        self.output = nn.Sequential(
            nn.LayerNorm(self.hidden_size * 2),
            nn.Linear(self.hidden_size * 2, self.hidden_size),
            nn.GELU(),
            nn.Linear(self.hidden_size, self.num_team_codes),
        )
        self._init_weights()

    def _init_weights(self):
        for module in list(self.state_encoder) + list(self.compact_encoder) + list(self.output):
            if isinstance(module, nn.Linear):
                initialize_weights(module, gain=1.0)

    def forward(self, state, compact):
        state = state.float()
        compact = compact.float()
        return self.output(torch.cat([self.state_encoder(state), self.compact_encoder(compact)], dim=-1))


class CompactIndividualDiscriminator(nn.Module):
    """Individual-skill discriminator q_d(z_i | o_i, c_tau, g_tau)."""

    def __init__(self, config):
        super().__init__()
        self.obs_dim = int(config.obs_dim)
        self.compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 128)))
        self.hidden_size = int(getattr(config, "hidden_size", 128))
        self.n_z = int(config.n_z)
        self.num_team_codes = int(getattr(config, "num_team_codes", getattr(config, "n_Z", 1)))
        self.obs_encoder = nn.Sequential(
            nn.LayerNorm(self.obs_dim),
            nn.Linear(self.obs_dim, self.hidden_size),
            nn.GELU(),
        )
        self.compact_encoder = nn.Sequential(
            nn.LayerNorm(self.compact_dim),
            nn.Linear(self.compact_dim, self.hidden_size),
            nn.GELU(),
        )
        self.team_embedding = nn.Embedding(self.num_team_codes, self.hidden_size)
        self.output = nn.Sequential(
            nn.LayerNorm(self.hidden_size * 3),
            nn.Linear(self.hidden_size * 3, self.hidden_size),
            nn.GELU(),
            nn.Linear(self.hidden_size, self.n_z),
        )
        self._init_weights()

    def _init_weights(self):
        initialize_weights(self.team_embedding, gain=1.0)
        for module in list(self.obs_encoder) + list(self.compact_encoder) + list(self.output):
            if isinstance(module, nn.Linear):
                initialize_weights(module, gain=1.0)

    def forward(self, observation, team_code, compact):
        if team_code.dtype != torch.long:
            team_code = team_code.long()
        team_code = team_code.clamp(min=0, max=self.num_team_codes - 1)
        observation = observation.float()
        compact = compact.float()
        return self.output(
            torch.cat(
                [
                    self.obs_encoder(observation),
                    self.compact_encoder(compact),
                    self.team_embedding(team_code),
                ],
                dim=-1,
            )
        )


class HorizonSkillEditor(nn.Module):
    """HA-CTSE high-level editor with bounded per-agent skill windows."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.n_agents = int(config.n_agents)
        self.n_z = int(config.n_z)
        self.n_Z = int(config.n_Z)
        self.hidden_size = int(getattr(config, "hidden_size", 128))
        self.compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 128)))
        self.team_code_dim = int(getattr(config, "team_code_dim", getattr(config, "embedding_dim", 128)))
        self.H_min = int(getattr(config, "H_min", 0))
        self.H_max = int(getattr(config, "H_max", 10**9))
        self.force_after_h_max = bool(getattr(config, "force_termination_after_H_max", True))
        self.assignment_mode = str(getattr(config, "high_level_assignment_mode", "parallel")).lower()
        self.use_discrete_lifetimes = bool(getattr(config, "use_discrete_skill_lifetimes", False))
        candidates = list(getattr(config, "skill_lifetime_candidates", (1, 2, 3, 5)))
        if not candidates:
            candidates = [1]
        self.num_duration_candidates = len(candidates)
        self.register_buffer(
            "duration_candidates",
            torch.as_tensor(candidates, dtype=torch.long),
            persistent=False,
        )

        self.compact_extractor = OPTCompactExtractor(config)
        self.bridge = CompactTeamBridge(config)

        self.obs_encoder = nn.Sequential(
            nn.Linear(int(config.obs_dim), self.hidden_size),
            nn.LayerNorm(self.hidden_size),
            nn.GELU(),
        )
        self.prev_skill_embedding = nn.Embedding(self.n_z, self.hidden_size)
        self.age_encoder = nn.Sequential(
            nn.Linear(1, self.hidden_size),
            nn.LayerNorm(self.hidden_size),
            nn.GELU(),
        )
        editor_input_dim = self.compact_dim + self.team_code_dim + self.hidden_size * 3
        self.editor_body = nn.Sequential(
            nn.Linear(editor_input_dim, self.hidden_size),
            nn.LayerNorm(self.hidden_size),
            nn.GELU(),
            nn.Linear(self.hidden_size, self.hidden_size),
            nn.LayerNorm(self.hidden_size),
            nn.GELU(),
        )
        self.term_head = nn.Linear(self.hidden_size, 2)
        self.skill_head = nn.Linear(self.hidden_size, self.n_z)
        self.duration_head = nn.Linear(self.hidden_size, self.num_duration_candidates)
        self.state_value_head = nn.Linear(self.compact_dim + self.team_code_dim, 1)
        self.agent_value_head = nn.Linear(self.hidden_size, 1)
        self.ar_skill_embedding = nn.Embedding(self.n_z, self.hidden_size)
        self.ar_edit_embedding = nn.Embedding(2, self.hidden_size)
        self.ar_context_proj = nn.Linear(self.hidden_size, self.hidden_size)
        self._init_weights()

    def _init_weights(self):
        for module in self.obs_encoder:
            if isinstance(module, nn.Linear):
                initialize_weights(module)
        initialize_weights(self.prev_skill_embedding)
        for module in self.age_encoder:
            if isinstance(module, nn.Linear):
                initialize_weights(module)
        for module in self.editor_body:
            if isinstance(module, nn.Linear):
                initialize_weights(module)
        initialize_weights(self.term_head, last_layer_gain=0.01)
        initialize_weights(self.skill_head, last_layer_gain=0.01)
        initialize_weights(self.duration_head, last_layer_gain=0.01)
        initialize_weights(self.state_value_head, last_layer_gain=0.01)
        initialize_weights(self.agent_value_head, last_layer_gain=0.01)
        initialize_weights(self.ar_skill_embedding)
        initialize_weights(self.ar_edit_embedding)
        initialize_weights(self.ar_context_proj, last_layer_gain=0.01)

    def _maybe_autoregressive_hidden(self, hidden, prev_skills, skill_ages, initial_assignment_mask,
                                     deterministic=False, candidate_skill=None, executed_edit_mask=None):
        if self.assignment_mode != "autoregressive":
            term_logits = torch.clamp(self.term_head(hidden), -50.0, 50.0)
            skill_logits = torch.clamp(self.skill_head(hidden), -50.0, 50.0)
            return hidden, term_logits, skill_logits

        batch_size = hidden.shape[0]
        device = hidden.device
        context = torch.zeros(batch_size, self.hidden_size, device=device)
        ar_hidden = []
        term_logits_list = []
        skill_logits_list = []
        safe_prev = prev_skills.clamp(min=0, max=self.n_z - 1).long()

        for agent_idx in range(self.n_agents):
            h_i = hidden[:, agent_idx] + self.ar_context_proj(context)
            term_logits_i = torch.clamp(self.term_head(h_i), -50.0, 50.0)
            skill_logits_i = torch.clamp(self.skill_head(h_i), -50.0, 50.0)
            ar_hidden.append(h_i)
            term_logits_list.append(term_logits_i)
            skill_logits_list.append(skill_logits_i)

            if candidate_skill is not None and executed_edit_mask is not None:
                exec_i = executed_edit_mask[:, agent_idx].bool()
                cand_i = candidate_skill[:, agent_idx].long()
                active_i = torch.where(exec_i, cand_i, safe_prev[:, agent_idx])
            else:
                masked_i, _, _ = self._masked_term_logits(
                    term_logits_i.unsqueeze(1),
                    skill_ages[:, agent_idx:agent_idx + 1],
                    initial_assignment_mask[:, agent_idx:agent_idx + 1],
                )
                term_dist_i = Categorical(logits=masked_i.squeeze(1))
                term_action_i = masked_i.squeeze(1).argmax(dim=-1) if deterministic else term_dist_i.sample()
                exec_i = term_action_i.bool() | initial_assignment_mask[:, agent_idx].bool()
                skill_dist_i = Categorical(logits=skill_logits_i)
                cand_i = skill_logits_i.argmax(dim=-1) if deterministic else skill_dist_i.sample()
                active_i = torch.where(exec_i, cand_i, safe_prev[:, agent_idx])

            context = context + self.ar_skill_embedding(active_i)
            context = context + self.ar_edit_embedding(exec_i.long())

        return (
            torch.stack(ar_hidden, dim=1),
            torch.stack(term_logits_list, dim=1),
            torch.stack(skill_logits_list, dim=1),
        )

    def _duration_outputs(self, hidden, executed_edit_mask, deterministic=False, forced_duration_candidate=None):
        batch_size, n_agents, _ = hidden.shape
        device = hidden.device
        zeros_float = torch.zeros(batch_size, n_agents, device=device)
        zeros_long = torch.zeros(batch_size, n_agents, dtype=torch.long, device=device)
        default_target = torch.ones(batch_size, n_agents, dtype=torch.long, device=device)

        if not self.use_discrete_lifetimes:
            logits = torch.zeros(batch_size, n_agents, 1, device=device)
            return {
                "duration_candidate": zeros_long,
                "duration_target": default_target,
                "duration_remaining": torch.zeros_like(default_target),
                "log_prob_duration": zeros_float,
                "entropy_duration": zeros_float,
                "duration_logits": logits,
            }

        logits = torch.clamp(self.duration_head(hidden), -50.0, 50.0)
        dist = Categorical(logits=logits)
        if forced_duration_candidate is not None:
            candidate = forced_duration_candidate.long().clamp(0, self.num_duration_candidates - 1)
        elif deterministic:
            candidate = logits.argmax(dim=-1)
        else:
            candidate = dist.sample()
        target = self.duration_candidates.to(device)[candidate]
        raw_log_prob = dist.log_prob(candidate)
        log_prob = torch.where(executed_edit_mask.bool(), raw_log_prob, torch.zeros_like(raw_log_prob))
        entropy = torch.where(executed_edit_mask.bool(), dist.entropy(), torch.zeros_like(raw_log_prob))
        remaining = torch.where(executed_edit_mask.bool(), target, torch.zeros_like(target))
        return {
            "duration_candidate": candidate,
            "duration_target": target,
            "duration_remaining": remaining,
            "log_prob_duration": log_prob,
            "entropy_duration": entropy,
            "duration_logits": logits,
        }

    def _assign_autoregressive_from_features(
        self,
        features,
        prev_skills,
        skill_ages,
        initial_assignment_mask,
        deterministic=False,
    ):
        base_hidden = features["hidden"]
        batch_size = base_hidden.shape[0]
        device = base_hidden.device
        context = torch.zeros(batch_size, self.hidden_size, device=device)
        safe_prev_skills = prev_skills.clamp(min=0, max=self.n_z - 1).long()

        ar_hidden = []
        term_logits_list = []
        skill_logits_list = []
        candidate_skill_list = []
        active_skill_list = []
        next_age_list = []
        requested_edit_list = []
        executed_edit_list = []
        term_log_prob_list = []
        skill_log_prob_list = []
        entropy_term_list = []
        entropy_skill_list = []
        h_min_list = []
        h_max_list = []

        for agent_idx in range(self.n_agents):
            h_i = base_hidden[:, agent_idx] + self.ar_context_proj(context)
            term_logits_i = torch.clamp(self.term_head(h_i), -50.0, 50.0)
            skill_logits_i = torch.clamp(self.skill_head(h_i), -50.0, 50.0)
            masked_term_logits_i, h_min_i, h_max_i = self._masked_term_logits(
                term_logits_i.unsqueeze(1),
                skill_ages[:, agent_idx:agent_idx + 1],
                initial_assignment_mask[:, agent_idx:agent_idx + 1],
            )
            masked_term_logits_i = masked_term_logits_i.squeeze(1)
            term_dist_i = Categorical(logits=masked_term_logits_i)
            requested_i = masked_term_logits_i.argmax(dim=-1) if deterministic else term_dist_i.sample()
            executed_i = requested_i.bool() | initial_assignment_mask[:, agent_idx].bool()
            term_log_prob_i = term_dist_i.log_prob(requested_i)
            term_log_prob_i = torch.where(
                initial_assignment_mask[:, agent_idx],
                torch.zeros_like(term_log_prob_i),
                term_log_prob_i,
            )
            entropy_term_i = term_dist_i.entropy()
            entropy_term_i = torch.where(
                initial_assignment_mask[:, agent_idx],
                torch.zeros_like(entropy_term_i),
                entropy_term_i,
            )

            skill_dist_i = Categorical(logits=skill_logits_i)
            candidate_i = skill_logits_i.argmax(dim=-1) if deterministic else skill_dist_i.sample()
            raw_skill_log_prob_i = skill_dist_i.log_prob(candidate_i)
            skill_log_prob_i = torch.where(executed_i, raw_skill_log_prob_i, torch.zeros_like(raw_skill_log_prob_i))
            active_i = torch.where(executed_i, candidate_i, safe_prev_skills[:, agent_idx])
            next_age_i = torch.where(executed_i, torch.zeros_like(skill_ages[:, agent_idx]), skill_ages[:, agent_idx] + 1)

            ar_hidden.append(h_i)
            term_logits_list.append(term_logits_i)
            skill_logits_list.append(skill_logits_i)
            candidate_skill_list.append(candidate_i)
            active_skill_list.append(active_i)
            next_age_list.append(next_age_i)
            requested_edit_list.append(requested_i.bool() | initial_assignment_mask[:, agent_idx])
            executed_edit_list.append(executed_i)
            term_log_prob_list.append(term_log_prob_i)
            skill_log_prob_list.append(skill_log_prob_i)
            entropy_term_list.append(entropy_term_i)
            entropy_skill_list.append(skill_dist_i.entropy())
            h_min_list.append(h_min_i.squeeze(1))
            h_max_list.append(h_max_i.squeeze(1))

            context = context + self.ar_skill_embedding(active_i)
            context = context + self.ar_edit_embedding(executed_i.long())

        hidden = torch.stack(ar_hidden, dim=1)
        active_skill = torch.stack(active_skill_list, dim=1)
        executed_mask = torch.stack(executed_edit_list, dim=1)
        duration = self._duration_outputs(hidden, executed_mask, deterministic=deterministic)
        return HACTSEOutput(
            compact=features["compact"],
            team_code=features["team_code"],
            team_vector=features["team_vector"],
            log_prob_team_code=features["log_prob_team_code"],
            entropy_team_code=features["entropy_team_code"],
            active_skill_prev=prev_skills,
            active_skill=active_skill,
            candidate_skill=torch.stack(candidate_skill_list, dim=1),
            skill_age_prev=skill_ages,
            skill_age=torch.stack(next_age_list, dim=1),
            requested_edit_mask=torch.stack(requested_edit_list, dim=1).float(),
            executed_edit_mask=executed_mask.float(),
            log_prob_term=torch.stack(term_log_prob_list, dim=1),
            log_prob_skill=torch.stack(skill_log_prob_list, dim=1),
            duration_candidate=duration["duration_candidate"],
            duration_target=duration["duration_target"],
            duration_remaining=duration["duration_remaining"],
            log_prob_duration=duration["log_prob_duration"],
            entropy_term=torch.stack(entropy_term_list, dim=1),
            entropy_skill=torch.stack(entropy_skill_list, dim=1),
            entropy_duration=duration["entropy_duration"],
            initial_assignment_mask=initial_assignment_mask.float(),
            state_values=features["state_values"],
            agent_values=self.agent_value_head(hidden).squeeze(-1),
            cd_loss=features["cd_loss"],
            cmi_loss=features["cmi_loss"],
            aggregation_entropy=features["aggregation_entropy"],
            h_min_mask=torch.stack(h_min_list, dim=1).float(),
            h_max_force_mask=torch.stack(h_max_list, dim=1).float(),
            term_logits=torch.stack(term_logits_list, dim=1),
            skill_logits=torch.stack(skill_logits_list, dim=1),
            duration_logits=duration["duration_logits"],
        ).as_dict()

    def _features(self, state, observations, prev_skills, skill_ages, forced_team_code=None, deterministic=False):
        compact, cd_loss, cmi_loss, _, aggregation_entropy = self.compact_extractor(state, observations)
        team_code, team_vector, log_prob_team_code, entropy_team_code, _ = self.bridge(
            compact,
            deterministic=deterministic,
            forced_team_code=forced_team_code,
        )

        batch_size, n_agents, _ = observations.shape
        safe_prev_skills = prev_skills.clamp(min=0, max=self.n_z - 1).long()
        obs_features = self.obs_encoder(observations.reshape(-1, observations.shape[-1])).reshape(
            batch_size, n_agents, self.hidden_size
        )
        prev_skill_features = self.prev_skill_embedding(safe_prev_skills)
        age_scale = max(float(self.H_max), 1.0)
        age_features = self.age_encoder((skill_ages.float() / age_scale).unsqueeze(-1))
        compact_features = compact.unsqueeze(1).expand(-1, n_agents, -1)
        team_features = team_vector.unsqueeze(1).expand(-1, n_agents, -1)
        editor_input = torch.cat(
            [compact_features, team_features, obs_features, prev_skill_features, age_features],
            dim=-1,
        )
        hidden = self.editor_body(editor_input)
        state_values = self.state_value_head(torch.cat([compact, team_vector], dim=-1))
        agent_values = self.agent_value_head(hidden).squeeze(-1)
        return {
            "compact": compact,
            "team_code": team_code,
            "team_vector": team_vector,
            "log_prob_team_code": log_prob_team_code,
            "entropy_team_code": entropy_team_code,
            "hidden": hidden,
            "state_values": state_values,
            "agent_values": agent_values,
            "cd_loss": cd_loss,
            "cmi_loss": cmi_loss,
            "aggregation_entropy": aggregation_entropy,
        }

    def _masked_term_logits(self, term_logits, skill_ages, initial_assignment_mask,
                            forced_keep_mask=None, forced_edit_mask=None):
        masked = term_logits.clone()
        normal_mask = ~initial_assignment_mask.bool()
        h_min_mask = (skill_ages < self.H_min) & normal_mask
        h_max_mask = (skill_ages >= self.H_max) & normal_mask & self.force_after_h_max
        if forced_keep_mask is not None:
            h_min_mask = h_min_mask | (forced_keep_mask.bool() & normal_mask)
        if forced_edit_mask is not None:
            h_max_mask = h_max_mask | (forced_edit_mask.bool() & normal_mask)
        masked[..., 1] = torch.where(
            h_min_mask,
            torch.full_like(masked[..., 1], -1e9),
            masked[..., 1],
        )
        masked[..., 0] = torch.where(
            h_max_mask,
            torch.full_like(masked[..., 0], -1e9),
            masked[..., 0],
        )
        return masked, h_min_mask, h_max_mask

    def assign_and_value_batch(
        self,
        state,
        observations,
        prev_skills,
        skill_ages,
        initial_assignment_mask,
        deterministic=False,
        forced_keep_mask=None,
        forced_edit_mask=None,
    ) -> Dict[str, torch.Tensor]:
        prev_skills = prev_skills.long()
        skill_ages = skill_ages.long()
        initial_assignment_mask = initial_assignment_mask.bool() | (prev_skills < 0)

        features = self._features(
            state,
            observations,
            prev_skills.clamp(min=0),
            skill_ages,
            deterministic=deterministic,
        )
        if self.assignment_mode == "autoregressive":
            return self._assign_autoregressive_from_features(
                features,
                prev_skills,
                skill_ages,
                initial_assignment_mask,
                deterministic=deterministic,
            )
        hidden, term_logits, skill_logits = self._maybe_autoregressive_hidden(
            features["hidden"],
            prev_skills,
            skill_ages,
            initial_assignment_mask,
            deterministic=deterministic,
        )
        agent_values = self.agent_value_head(hidden).squeeze(-1)

        masked_term_logits, h_min_mask, h_max_mask = self._masked_term_logits(
            term_logits,
            skill_ages,
            initial_assignment_mask,
            forced_keep_mask=forced_keep_mask,
            forced_edit_mask=forced_edit_mask,
        )
        term_dist = Categorical(logits=masked_term_logits)
        requested_edit = masked_term_logits.argmax(dim=-1) if deterministic else term_dist.sample()
        requested_edit_mask = requested_edit.bool() | initial_assignment_mask
        executed_edit_mask = requested_edit_mask
        term_log_prob = term_dist.log_prob(requested_edit)
        term_log_prob = torch.where(initial_assignment_mask, torch.zeros_like(term_log_prob), term_log_prob)
        entropy_term = term_dist.entropy()
        entropy_term = torch.where(initial_assignment_mask, torch.zeros_like(entropy_term), entropy_term)

        skill_dist = Categorical(logits=skill_logits)
        candidate_skill = skill_logits.argmax(dim=-1) if deterministic else skill_dist.sample()
        raw_skill_log_prob = skill_dist.log_prob(candidate_skill)
        log_prob_skill = torch.where(executed_edit_mask, raw_skill_log_prob, torch.zeros_like(raw_skill_log_prob))
        entropy_skill = skill_dist.entropy()

        safe_prev_skills = prev_skills.clamp(min=0)
        active_skill = torch.where(executed_edit_mask, candidate_skill, safe_prev_skills)
        next_age = torch.where(executed_edit_mask, torch.zeros_like(skill_ages), skill_ages + 1)
        duration = self._duration_outputs(hidden, executed_edit_mask, deterministic=deterministic)

        return HACTSEOutput(
            compact=features["compact"],
            team_code=features["team_code"],
            team_vector=features["team_vector"],
            log_prob_team_code=features["log_prob_team_code"],
            entropy_team_code=features["entropy_team_code"],
            active_skill_prev=prev_skills,
            active_skill=active_skill,
            candidate_skill=candidate_skill,
            skill_age_prev=skill_ages,
            skill_age=next_age,
            requested_edit_mask=requested_edit_mask.float(),
            executed_edit_mask=executed_edit_mask.float(),
            log_prob_term=term_log_prob,
            log_prob_skill=log_prob_skill,
            duration_candidate=duration["duration_candidate"],
            duration_target=duration["duration_target"],
            duration_remaining=duration["duration_remaining"],
            log_prob_duration=duration["log_prob_duration"],
            entropy_term=entropy_term,
            entropy_skill=entropy_skill,
            entropy_duration=duration["entropy_duration"],
            initial_assignment_mask=initial_assignment_mask.float(),
            state_values=features["state_values"],
            agent_values=agent_values,
            cd_loss=features["cd_loss"],
            cmi_loss=features["cmi_loss"],
            aggregation_entropy=features["aggregation_entropy"],
            h_min_mask=h_min_mask.float(),
            h_max_force_mask=h_max_mask.float(),
            term_logits=term_logits,
            skill_logits=skill_logits,
            duration_logits=duration["duration_logits"],
        ).as_dict()

    def evaluate_training_batch(
        self,
        state,
        observations,
        team_code,
        active_skill_prev,
        candidate_skill,
        skill_age_prev,
        executed_edit_mask,
        initial_assignment_mask,
        deterministic=False,
        duration_candidate=None,
    ) -> Dict[str, torch.Tensor]:
        team_code = team_code.long()
        active_skill_prev = active_skill_prev.long()
        candidate_skill = candidate_skill.long()
        skill_age_prev = skill_age_prev.long()
        executed_edit_mask = executed_edit_mask.bool()
        initial_assignment_mask = initial_assignment_mask.bool() | (active_skill_prev < 0)

        features = self._features(
            state,
            observations,
            active_skill_prev.clamp(min=0),
            skill_age_prev,
            forced_team_code=team_code,
            deterministic=deterministic,
        )
        hidden, term_logits, skill_logits = self._maybe_autoregressive_hidden(
            features["hidden"],
            active_skill_prev,
            skill_age_prev,
            initial_assignment_mask,
            deterministic=deterministic,
            candidate_skill=candidate_skill,
            executed_edit_mask=executed_edit_mask,
        )
        agent_values = self.agent_value_head(hidden).squeeze(-1)

        masked_term_logits, h_min_mask, h_max_mask = self._masked_term_logits(
            term_logits,
            skill_age_prev,
            initial_assignment_mask,
        )
        term_dist = Categorical(logits=masked_term_logits)
        term_action = executed_edit_mask.long()
        log_prob_term = term_dist.log_prob(term_action)
        log_prob_term = torch.where(initial_assignment_mask, torch.zeros_like(log_prob_term), log_prob_term)
        entropy_term = term_dist.entropy()
        entropy_term = torch.where(initial_assignment_mask, torch.zeros_like(entropy_term), entropy_term)

        skill_dist = Categorical(logits=skill_logits)
        raw_skill_log_prob = skill_dist.log_prob(candidate_skill)
        log_prob_skill = torch.where(executed_edit_mask, raw_skill_log_prob, torch.zeros_like(raw_skill_log_prob))
        duration = self._duration_outputs(
            hidden,
            executed_edit_mask,
            deterministic=deterministic,
            forced_duration_candidate=duration_candidate,
        )

        return {
            "compact": features["compact"],
            "team_code": features["team_code"],
            "log_prob_team_code": features["log_prob_team_code"],
            "entropy_team_code": features["entropy_team_code"],
            "log_prob_term": log_prob_term,
            "log_prob_skill": log_prob_skill,
            "log_prob_duration": duration["log_prob_duration"],
            "entropy_term": entropy_term,
            "entropy_skill": skill_dist.entropy(),
            "entropy_duration": duration["entropy_duration"],
            "state_values": features["state_values"],
            "agent_values": agent_values,
            "cd_loss": features["cd_loss"],
            "cmi_loss": features["cmi_loss"],
            "aggregation_entropy": features["aggregation_entropy"],
            "h_min_mask": h_min_mask.float(),
            "h_max_force_mask": h_max_mask.float(),
            "term_logits": term_logits,
            "skill_logits": skill_logits,
            "duration_logits": duration["duration_logits"],
        }
