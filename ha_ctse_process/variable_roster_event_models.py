"""Model owners for the variable-roster event runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from hmasd.r_mappo_utils import ACTLayer, MLPBase, RNNLayer, check
from ha_ctse_process import variable_roster_event_support


@dataclass(frozen=True)
class MSSRSelectiveSPFPartition:
    """The production-owned selective state read for one MSSR decision.

    ``S`` is the current slow/set context, ``P`` is the authenticated retained
    partner history, and ``F`` is the owner's fast pre-recurrence control
    state.  The object is deliberately typed rather than a tuple of labels:
    :meth:`EventCommitmentPolicy.first_logits` consumes all three tensors when
    constructing the production action logits.
    """

    slow_context: torch.Tensor
    partner_history: torch.Tensor
    fast_control: torch.Tensor
    owners: tuple[str, str, str] = (
        "unit.slow_context",
        "unit.partner_interaction",
        "unit.fast_control",
    )

    def validate(self, *, summary_dim: int, high_hidden_dim: int) -> None:
        if self.owners != (
            "unit.slow_context",
            "unit.partner_interaction",
            "unit.fast_control",
        ):
            raise ValueError("MSSR S/P/F partition owners are not registered")
        if tuple(self.slow_context.shape) != (1, int(summary_dim)):
            raise ValueError("MSSR S partition has the wrong shape")
        if tuple(self.partner_history.shape) != (1, 1):
            raise ValueError("MSSR P partition has the wrong shape")
        if tuple(self.fast_control.shape) != (1, int(high_hidden_dim)):
            raise ValueError("MSSR F partition has the wrong shape")
        tensors = (
            self.slow_context,
            self.partner_history,
            self.fast_control,
        )
        if len({(item.device, item.dtype) for item in tensors}) != 1:
            raise ValueError("MSSR S/P/F partition tensors must share device/dtype")
        if not all(bool(torch.all(torch.isfinite(item)).item()) for item in tensors):
            raise ValueError("MSSR S/P/F partition contains a non-finite value")


class EventCommitmentPolicy(nn.Module):
    """One parameter graph used by both F0 and F1."""

    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        member_hidden_dim: int,
        high_hidden_dim: int,
        skill_embedding_dim: int,
        partner_first_action: bool = False,
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(n_skills)
        self.member_hidden_dim = int(member_hidden_dim)
        self.high_hidden_dim = int(high_hidden_dim)
        self.skill_embedding_dim = int(skill_embedding_dim)
        self.summary_dim = self.member_hidden_dim + 1
        self.partner_first_action = bool(partner_first_action)

        self.skill_embedding = nn.Embedding(self.n_skills, self.skill_embedding_dim)
        member_input_dim = self.obs_dim + self.skill_embedding_dim + 3
        self.member_encoder = nn.Sequential(
            nn.LayerNorm(member_input_dim),
            nn.Linear(member_input_dim, self.member_hidden_dim),
            nn.GELU(),
            nn.Linear(self.member_hidden_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        self.high_rnn = nn.GRUCell(
            self.member_hidden_dim + self.summary_dim,
            self.high_hidden_dim,
        )
        self.decoder_hidden = nn.Sequential(
            nn.Linear(self.high_hidden_dim + self.summary_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        self.skill_head = nn.Linear(self.member_hidden_dim, self.n_skills)
        if self.partner_first_action:
            # Seq-12 support-native pre-recurrence action head.  Emits
            # first-logits from the pre-recurrence hidden state and the owner's
            # historical partner-interaction value (P) BEFORE the GRU update, so
            # first_logits_tick < recurrent_update_tick.  Constructed LAST and
            # only when enabled, so a disabled policy has a byte-identical
            # parameter set and identical initialization RNG consumption -- the
            # existing FOLR / continuous-roster runs are unperturbed.  The input
            # carries one extra scalar slot for the historical P value.  (This is
            # the separate support-native P precondition, not the full skill
            # commitment contract, so no full-contract binding token is used.)
            self.first_decoder = nn.Sequential(
                nn.Linear(
                    self.high_hidden_dim + self.summary_dim + 1,
                    self.member_hidden_dim,
                ),
                nn.GELU(),
            )
            self.first_head = nn.Linear(self.member_hidden_dim, self.n_skills)

    def encode_members(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        ages: torch.Tensor,
        event_flags: torch.Tensor,
    ) -> torch.Tensor:
        observations = observations.float()
        skills = skills.long().reshape(-1)
        ages = ages.float().reshape(-1)
        event_flags = event_flags.bool().reshape(-1, 2)
        if observations.ndim != 2 or observations.shape[1] != self.obs_dim:
            raise ValueError("active observations have the wrong shape")
        if observations.shape[0] != skills.shape[0]:
            raise ValueError("active observation/skill row mismatch")
        genuine_join = event_flags[:, 0]
        undefined = skills < 0
        if bool(torch.any(undefined & ~genuine_join).item()):
            raise ValueError("only a genuine join may have an undefined skill")
        safe_skills = skills.clamp(0, self.n_skills - 1)
        skill_features = self.skill_embedding(safe_skills)
        skill_features = torch.where(
            undefined.unsqueeze(-1),
            torch.zeros_like(skill_features),
            skill_features,
        )
        member_input = torch.cat(
            (
                observations,
                skill_features,
                variable_roster_event_support.normalized_log_age(ages).unsqueeze(-1),
                event_flags.to(dtype=torch.float32),
            ),
            dim=-1,
        )
        return self.member_encoder(member_input)

    @staticmethod
    def set_summary(member_embeddings: torch.Tensor) -> torch.Tensor:
        if member_embeddings.ndim != 2 or member_embeddings.shape[0] <= 0:
            raise ValueError("set summary requires at least one active member")
        log_count = torch.log1p(
            torch.tensor(
                float(member_embeddings.shape[0]),
                dtype=member_embeddings.dtype,
                device=member_embeddings.device,
            )
        ).reshape(1)
        return torch.cat((member_embeddings.sum(dim=0), log_count), dim=0)

    def logits(
        self,
        member_embedding: torch.Tensor,
        selected_summary: torch.Tensor,
        pre_hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        member_embedding = member_embedding.reshape(1, self.member_hidden_dim)
        selected_summary = selected_summary.reshape(1, self.summary_dim)
        pre_hidden = pre_hidden.reshape(1, self.high_hidden_dim)
        new_hidden = self.high_rnn(
            torch.cat((member_embedding, selected_summary), dim=-1),
            pre_hidden,
        )
        hidden = self.decoder_hidden(torch.cat((new_hidden, selected_summary), dim=-1))
        return self.skill_head(hidden).squeeze(0), new_hidden.squeeze(0)

    def selective_spf_partition(
        self,
        selected_summary: torch.Tensor,
        pre_hidden: torch.Tensor,
        partner_p: torch.Tensor | float,
    ) -> MSSRSelectiveSPFPartition:
        """Bind the registered S/P/F owners to the action-read tensors."""

        slow = selected_summary.reshape(1, self.summary_dim)
        fast = pre_hidden.reshape(1, self.high_hidden_dim)
        partner = torch.as_tensor(
            partner_p, dtype=fast.dtype, device=fast.device
        ).reshape(1, 1)
        partition = MSSRSelectiveSPFPartition(
            slow_context=slow,
            partner_history=partner,
            fast_control=fast,
        )
        partition.validate(
            summary_dim=self.summary_dim,
            high_hidden_dim=self.high_hidden_dim,
        )
        return partition

    def first_logits(
        self,
        member_embedding: torch.Tensor,
        selected_summary: torch.Tensor,
        pre_hidden: torch.Tensor,
        partner_p: torch.Tensor | float | None = None,
        *,
        partition: MSSRSelectiveSPFPartition | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Seq-12 support-native pre-recurrence action head.

        Produces the action logits from the PRE-recurrence hidden state and the
        owner's historical partner-interaction value ``partner_p`` BEFORE the
        recurrent update runs, so the returned logits carry no computational
        dependence on the post-recurrence hidden value.  The recurrent update
        still executes and its ``new_hidden`` is returned for the state carry,
        exactly as ``logits`` does, but the action head does not read it.
        """
        if not self.partner_first_action:
            raise RuntimeError(
                "first_logits requires the policy to be built with "
                "partner_first_action=True"
            )
        member_embedding = member_embedding.reshape(1, self.member_hidden_dim)
        selected_summary = selected_summary.reshape(1, self.summary_dim)
        pre_hidden = pre_hidden.reshape(1, self.high_hidden_dim)
        if partition is not None and partner_p is not None:
            raise ValueError("supply either MSSR partition or partner_p, not both")
        if partition is None:
            partition = self.selective_spf_partition(
                selected_summary,
                pre_hidden,
                0.0 if partner_p is None else partner_p,
            )
        partition.validate(
            summary_dim=self.summary_dim,
            high_hidden_dim=self.high_hidden_dim,
        )
        # Action logits FIRST.  The typed production partition is the sole
        # action-head input, so S/P/F are consumed state rather than audit-only
        # labels.  The member embedding is used only by the later recurrence.
        first_hidden = self.first_decoder(
            torch.cat(
                (
                    partition.fast_control,
                    partition.slow_context,
                    partition.partner_history,
                ),
                dim=-1,
            )
        )
        first = self.first_head(first_hidden)
        # Recurrent update AFTERWARDS; carried but not read by the action head.
        new_hidden = self.high_rnn(
            torch.cat((member_embedding, selected_summary), dim=-1),
            pre_hidden,
        )
        return first.squeeze(0), new_hidden.squeeze(0)

    def zero_summary_path(self) -> None:
        """Create the registered action-independent reduction control."""

        with torch.no_grad():
            self.high_rnn.weight_ih[:, self.member_hidden_dim :] = 0.0
            first = self.decoder_hidden[0]
            first.weight[:, self.high_hidden_dim :] = 0.0


class EventHighCritic(nn.Module):
    def __init__(
        self,
        *,
        critic_member_dim: int,
        critic_global_dim: int,
        n_skills: int,
        member_hidden_dim: int,
        high_hidden_dim: int,
        skill_embedding_dim: int,
    ) -> None:
        super().__init__()
        self.critic_member_dim = int(critic_member_dim)
        self.critic_global_dim = int(critic_global_dim)
        self.n_skills = int(n_skills)
        self.member_hidden_dim = int(member_hidden_dim)
        self.high_hidden_dim = int(high_hidden_dim)
        self.skill_embedding_dim = int(skill_embedding_dim)
        self.skill_embedding = nn.Embedding(self.n_skills, self.skill_embedding_dim)
        input_dim = (
            self.critic_member_dim
            + self.skill_embedding_dim
            + 3
        )
        self.member_encoder = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, self.member_hidden_dim),
            nn.GELU(),
        )
        value_input_dim = (
            2 * self.member_hidden_dim
            + 1
            + self.critic_global_dim
            + self.high_hidden_dim
            + len(variable_roster_event_support.BOUNDARY_KINDS)
        )
        self.value = nn.Sequential(
            nn.Linear(value_input_dim, self.member_hidden_dim),
            nn.GELU(),
            nn.Linear(self.member_hidden_dim, 1),
        )

    def values(
        self,
        critic_member_features: torch.Tensor,
        skills: torch.Tensor,
        ages: torch.Tensor,
        event_flags: torch.Tensor,
        high_hidden: torch.Tensor,
        critic_global_features: torch.Tensor,
        boundary_kind: str,
    ) -> torch.Tensor:
        if boundary_kind not in variable_roster_event_support.BOUNDARY_KINDS:
            raise ValueError(f"unknown critic boundary kind {boundary_kind!r}")
        flags = event_flags.bool().reshape(-1, 2)
        raw_skills = skills.long().reshape(-1)
        genuine_join = flags[:, 0]
        undefined = raw_skills < 0
        if bool(torch.any(undefined & ~genuine_join).item()):
            raise ValueError("only a genuine join may have an undefined critic skill")
        safe_skills = raw_skills.clamp(0, self.n_skills - 1)
        skill_features = self.skill_embedding(safe_skills)
        skill_features = torch.where(
            undefined.unsqueeze(-1),
            torch.zeros_like(skill_features),
            skill_features,
        )
        member_input = torch.cat(
            (
                critic_member_features.float(),
                skill_features,
                variable_roster_event_support.normalized_log_age(
                    ages.float().reshape(-1)
                ).unsqueeze(-1),
                flags.to(dtype=torch.float32),
            ),
            dim=-1,
        )
        encoded = self.member_encoder(member_input)
        set_sum = encoded.sum(dim=0, keepdim=True).expand_as(encoded)
        log_count = torch.log1p(
            torch.tensor(
                float(encoded.shape[0]), dtype=encoded.dtype, device=encoded.device
            )
        ).expand(encoded.shape[0], 1)
        global_rows = critic_global_features.float().reshape(1, -1).expand(
            encoded.shape[0], -1
        )
        kind = torch.zeros(
            encoded.shape[0], len(variable_roster_event_support.BOUNDARY_KINDS), dtype=encoded.dtype, device=encoded.device
        )
        kind[:, variable_roster_event_support.BOUNDARY_KINDS.index(boundary_kind)] = 1.0
        return self.value(
            torch.cat(
                (
                    encoded,
                    set_sum,
                    log_count,
                    global_rows,
                    high_hidden.float(),
                    kind,
                ),
                dim=-1,
            )
        ).squeeze(-1)


class Discrete:
    def __init__(self, n: int) -> None:
        self.n = int(n)


class Box:
    def __init__(self, shape: Sequence[int]) -> None:
        self.shape = tuple(int(value) for value in shape)


class EventLowActor(nn.Module):
    """Trainable actor-only ragged policy with the strict HMASD actor stack."""

    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        action_dim: int,
        hidden_dim: int,
        action_space_type: str = "discrete",
        device: str | torch.device = "cpu",
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_skills = int(n_skills)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.action_space_type = str(action_space_type)
        self.device = torch.device(device)

        class Args:
            pass

        args = Args()
        args.hidden_size = self.hidden_dim
        args.gain = 0.01
        args.use_orthogonal = True
        args.use_policy_active_masks = True
        args.use_naive_recurrent_policy = False
        args.use_recurrent_policy = True
        args.recurrent_N = 1
        args.use_feature_normalization = False
        args.use_popart = False
        args.continuous_action_distribution = "tanh_gaussian"
        args.continuous_logstd_init = -1.0
        args.continuous_logstd_min = -5.0
        args.continuous_logstd_max = 0.0
        self.actor_base = MLPBase(args, (self.obs_dim,))
        self.actor_film = nn.Linear(self.n_skills, 2 * self.hidden_dim)
        self.actor_rnn = RNNLayer(
            self.hidden_dim, self.hidden_dim, args.recurrent_N, args.use_orthogonal
        )
        action_space = (
            Discrete(self.action_dim)
            if self.action_space_type == "discrete"
            else Box((self.action_dim,))
        )
        self.actor_act = ACTLayer(
            action_space, self.hidden_dim, args.use_orthogonal, args.gain, args
        )
        self.to(self.device)

    @staticmethod
    def _squeeze_logp(logp: torch.Tensor) -> torch.Tensor:
        if logp.ndim > 1 and logp.shape[-1] == 1:
            return logp.squeeze(-1)
        return logp

    def _features(self, observations: torch.Tensor, skills: torch.Tensor) -> torch.Tensor:
        observations = check(observations).to(dtype=torch.float32, device=self.device)
        skills = check(skills).to(dtype=torch.long, device=self.device)
        features = self.actor_base(observations)
        film = self.actor_film(F.one_hot(skills, num_classes=self.n_skills).float())
        gamma, beta = torch.chunk(film, 2, dim=-1)
        return gamma * features + beta

    def actor_step(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        hidden: torch.Tensor,
        *,
        deterministic: bool = False,
        sampling_uniforms: np.ndarray | torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        observations = observations.to(self.device)
        skills = skills.to(self.device)
        hidden = hidden.to(dtype=torch.float32, device=self.device)
        features = self._features(observations, skills)
        masks = torch.ones(features.shape[0], 1, dtype=torch.float32, device=self.device)
        features, new_hidden = self.actor_rnn(features, hidden, masks)
        if self.action_space_type == "discrete":
            distribution = self.actor_act.action_out(features)
            if deterministic:
                actions = distribution.mode()
            else:
                if sampling_uniforms is None:
                    raise ValueError("discrete event low sampling requires owned uniforms")
                uniforms = np.asarray(
                    sampling_uniforms.detach().cpu().numpy()
                    if isinstance(sampling_uniforms, torch.Tensor)
                    else sampling_uniforms,
                    dtype=np.float64,
                ).reshape(-1)
                if uniforms.shape != (features.shape[0],):
                    raise ValueError("event low sampling-uniform shape mismatch")
                probability_rows = distribution.probs.detach().cpu().numpy()
                sampled = [
                    variable_roster_event_support.inverse_cdf_action(probability, uniform)
                    for probability, uniform in zip(probability_rows, uniforms)
                ]
                actions = torch.as_tensor(
                    sampled, dtype=torch.long, device=features.device
                ).unsqueeze(-1)
            logp = distribution.log_probs(actions)
            actions = actions.squeeze(-1)
        else:
            if sampling_uniforms is not None:
                raise ValueError("continuous event low policy does not accept discrete uniforms")
            actions, logp = self.actor_act(features, deterministic=deterministic)
        return actions, self._squeeze_logp(logp), new_hidden

    def actor_replay(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        logp, _entropy, final_hidden = self.actor_replay_with_entropy(
            observations,
            skills,
            actions,
            initial_hidden,
            valid_masks,
            reset_masks,
        )
        return logp, final_hidden

    def actor_replay_with_entropy(
        self,
        observations: torch.Tensor,
        skills: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
        *,
        return_entropy_rows: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        observations = observations.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        actions = actions.to(device=self.device)
        valid_masks = valid_masks.to(dtype=torch.float32, device=self.device).reshape(
            observations.shape[0], observations.shape[1], 1
        )
        reset_masks = reset_masks.to(dtype=torch.float32, device=self.device).reshape_as(
            valid_masks
        )
        features = self._features(observations, skills)
        rnn_masks = torch.ones_like(valid_masks)
        if observations.shape[0] > 1:
            rnn_masks[1:] = reset_masks[:-1]
        features, final_hidden = self.actor_rnn(
            features,
            initial_hidden.to(dtype=torch.float32, device=self.device),
            rnn_masks,
        )
        flat_actions = (
            actions.reshape(-1, 1)
            if self.action_space_type == "discrete"
            else actions.reshape(-1, self.action_dim)
        )
        flat_features = features.reshape(-1, self.hidden_dim)
        if return_entropy_rows:
            if self.action_space_type != "discrete":
                raise ValueError("row-wise event entropy is restricted to discrete actions")
            distribution = self.actor_act.action_out(flat_features)
            logp = distribution.log_probs(flat_actions)
            entropy = distribution.entropy().reshape(observations.shape[:2])
        else:
            logp, entropy = self.actor_act.evaluate_actions(
                flat_features,
                flat_actions,
                active_masks=valid_masks.reshape(-1, 1),
            )
        logp = self._squeeze_logp(logp).reshape(observations.shape[:2])
        return logp, entropy, final_hidden


class EventActiveSetLowCritic(nn.Module):
    """Separate active-set critic; no identity or fixed roster axis."""

    def __init__(
        self,
        *,
        critic_member_dim: int,
        critic_global_dim: int,
        n_skills: int,
        hidden_dim: int,
        skill_embedding_dim: int,
        device: str | torch.device = "cpu",
    ) -> None:
        super().__init__()
        self.critic_member_dim = int(critic_member_dim)
        self.critic_global_dim = int(critic_global_dim)
        self.n_skills = int(n_skills)
        self.hidden_dim = int(hidden_dim)
        self.device = torch.device(device)
        self.skill_embedding = nn.Embedding(self.n_skills, int(skill_embedding_dim))
        self.member_encoder = nn.Sequential(
            nn.Linear(self.critic_member_dim + int(skill_embedding_dim), self.hidden_dim),
            nn.GELU(),
        )
        self.source_dim = self.hidden_dim + 1 + self.critic_global_dim
        self.critic_input = nn.Sequential(
            nn.Linear(self.hidden_dim + self.source_dim, self.hidden_dim),
            nn.GELU(),
        )
        self.critic_rnn = nn.GRUCell(self.hidden_dim, self.hidden_dim)
        self.value_head = nn.Linear(self.hidden_dim, 1)
        self.to(self.device)

    def _member_encoded(
        self, member_features: torch.Tensor, skills: torch.Tensor
    ) -> torch.Tensor:
        member_features = member_features.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        return self.member_encoder(
            torch.cat((member_features, self.skill_embedding(skills)), dim=-1)
        )

    def critic_step(
        self,
        member_features: torch.Tensor,
        skills: torch.Tensor,
        env_ptr: torch.Tensor,
        global_features: torch.Tensor,
        hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = self._member_encoded(member_features, skills)
        env_ptr = env_ptr.to(dtype=torch.long, device=self.device)
        global_features = global_features.to(dtype=torch.float32, device=self.device)
        env_count = int(env_ptr.numel()) - 1
        if env_count <= 0 or global_features.shape[0] != env_count:
            raise ValueError("event low critic environment pointers are malformed")
        counts = env_ptr[1:] - env_ptr[:-1]
        if bool(torch.any(counts <= 0).item()):
            raise ValueError("event low critic does not admit an empty active set")
        segment_ids = torch.repeat_interleave(
            torch.arange(env_count, dtype=torch.long, device=self.device),
            counts,
            output_size=encoded.shape[0],
        )
        if segment_ids.shape[0] != encoded.shape[0]:
            raise ValueError("event low critic pointers do not cover active members")
        set_sums = torch.zeros(
            env_count,
            self.hidden_dim,
            dtype=encoded.dtype,
            device=self.device,
        ).index_add(0, segment_ids, encoded)
        log_counts = torch.log1p(counts.to(dtype=encoded.dtype)).unsqueeze(-1)
        per_environment_source = torch.cat(
            (set_sums, log_counts, global_features), dim=-1
        )
        source = per_environment_source.index_select(0, segment_ids)
        features = self.critic_input(torch.cat((encoded, source), dim=-1))
        new_hidden = self.critic_rnn(features, hidden.to(self.device).float())
        return self.value_head(new_hidden).squeeze(-1), new_hidden, source

    def critic_replay(
        self,
        member_features: torch.Tensor,
        skills: torch.Tensor,
        source_summary: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        member_features = member_features.to(dtype=torch.float32, device=self.device)
        skills = skills.to(dtype=torch.long, device=self.device)
        source_summary = source_summary.to(dtype=torch.float32, device=self.device)
        valid_masks = valid_masks.to(dtype=torch.float32, device=self.device)
        reset_masks = reset_masks.to(dtype=torch.float32, device=self.device)
        hidden = initial_hidden.to(dtype=torch.float32, device=self.device)
        values: list[torch.Tensor] = []
        for step in range(member_features.shape[0]):
            if step > 0:
                hidden = hidden * reset_masks[step - 1].reshape(-1, 1)
            encoded = self._member_encoded(member_features[step], skills[step])
            features = self.critic_input(
                torch.cat((encoded, source_summary[step]), dim=-1)
            )
            proposed = self.critic_rnn(features, hidden)
            valid = valid_masks[step].reshape(-1, 1)
            hidden = proposed * valid + hidden * (1.0 - valid)
            values.append(self.value_head(hidden).squeeze(-1))
        return torch.stack(values), hidden

    def critic_replay_from_active_sets(
        self,
        active_member_features: torch.Tensor,
        active_skills: torch.Tensor,
        active_masks: torch.Tensor,
        focal_indices: torch.Tensor,
        global_features: torch.Tensor,
        initial_hidden: torch.Tensor,
        valid_masks: torch.Tensor,
        reset_masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Re-encode each anonymous active set under current critic parameters."""

        features = active_member_features.to(dtype=torch.float32, device=self.device)
        skills = active_skills.to(dtype=torch.long, device=self.device)
        masks = active_masks.to(dtype=torch.bool, device=self.device)
        focal = focal_indices.to(dtype=torch.long, device=self.device)
        globals_ = global_features.to(dtype=torch.float32, device=self.device)
        valid = valid_masks.to(dtype=torch.float32, device=self.device)
        reset = reset_masks.to(dtype=torch.float32, device=self.device)
        if features.ndim != 4 or features.shape[-1] != self.critic_member_dim:
            raise ValueError("raw active critic features have the wrong shape")
        if skills.shape != features.shape[:3] or masks.shape != features.shape[:3]:
            raise ValueError("raw active critic skills/masks do not match features")
        if focal.shape != features.shape[:2]:
            raise ValueError("raw active critic focal indices have the wrong shape")
        if globals_.shape != (*features.shape[:2], self.critic_global_dim):
            raise ValueError("raw active critic global features have the wrong shape")
        if bool(torch.any(masks.sum(dim=-1) <= 0).item()):
            raise ValueError("raw active critic replay does not admit an empty set")
        if bool(
            torch.any(
                (focal < 0)
                | (focal >= features.shape[2])
                | ~torch.gather(masks, 2, focal.unsqueeze(-1)).squeeze(-1)
            ).item()
        ):
            raise ValueError("raw active critic focal row is invalid")

        time_steps, batch_size, max_active, _ = features.shape
        encoded = self._member_encoded(
            features.reshape(time_steps * batch_size * max_active, -1),
            skills.reshape(-1),
        ).reshape(time_steps, batch_size, max_active, self.hidden_dim)
        float_masks = masks.to(dtype=encoded.dtype).unsqueeze(-1)
        set_sum = (encoded * float_masks).sum(dim=2)
        count = torch.log1p(masks.sum(dim=2).to(dtype=encoded.dtype)).unsqueeze(-1)
        source = torch.cat((set_sum, count, globals_), dim=-1)
        gather_index = focal.unsqueeze(-1).unsqueeze(-1).expand(
            time_steps, batch_size, 1, self.hidden_dim
        )
        focal_encoded = torch.gather(encoded, 2, gather_index).squeeze(2)
        hidden = initial_hidden.to(dtype=torch.float32, device=self.device)
        values: list[torch.Tensor] = []
        for step in range(time_steps):
            if step > 0:
                hidden = hidden * reset[step - 1].reshape(-1, 1)
            critic_input = self.critic_input(
                torch.cat((focal_encoded[step], source[step]), dim=-1)
            )
            proposed = self.critic_rnn(critic_input, hidden)
            step_valid = valid[step].reshape(-1, 1)
            hidden = proposed * step_valid + hidden * (1.0 - step_valid)
            values.append(self.value_head(hidden).squeeze(-1))
        return torch.stack(values), hidden, source


class SuppliedExecutorLowSentinel(nn.Module):
    """Parameterless, state-free guard replacing both low graphs in supplied mode."""

    def __init__(self, path_name: str, device: str | torch.device) -> None:
        super().__init__()
        self.path_name = str(path_name)
        self.device = torch.device(device)

    def _fail(self, *_args: Any, **_kwargs: Any):
        raise RuntimeError(
            f"{self.path_name} is unavailable in supplied-executor/no-low-path mode"
        )

    forward = _fail
    actor_step = _fail
    actor_replay = _fail
    actor_replay_with_entropy = _fail
    critic_step = _fail
    critic_replay = _fail
    critic_replay_from_active_sets = _fail
